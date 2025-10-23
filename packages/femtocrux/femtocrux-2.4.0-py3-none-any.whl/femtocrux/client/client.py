from collections.abc import Iterable
from dataclasses import dataclass
import docker
from getpass import getpass
import google.protobuf
import grpc
import logging
import numpy as np
import os
import pickle
import queue
import sys
import time
from typing import Any, List, Tuple
from contextlib import contextmanager

from fmot.fqir import GraphProto

from femtocrux.util.utils import (
    get_channel_options,
    serialize_sim_inputs_message,
    deserialize_simulation_output,
)

# GRPC artifacts
import femtocrux.grpc.compiler_service_pb2 as cs_pb2
import femtocrux.grpc.compiler_service_pb2_grpc as cs_pb2_grpc

# Docker info
__docker_registry__ = "ghcr.io"


def _get_docker_image_name() -> str:
    """
    Returns the docker image name. For testing, override with the
    FEMTOCRUX_SERVER_IMAGE_NAME environment variable.
    """
    try:
        return os.environ["FEMTOCRUX_SERVER_IMAGE_NAME"]
    except KeyError:
        from femtocrux.version import __version__

        ORG = "femtosense"
        IMAGE = "femtocrux"
        remote_image_name = "%s/%s/%s:%s" % (
            __docker_registry__,
            ORG,
            IMAGE,
            __version__,
        )
        return remote_image_name


__docker_image_name__ = _get_docker_image_name()


# Set up logging
def _init_logger():
    """Init a basic logger to stderr."""
    logger = logging.getLogger(__name__)
    logger.setLevel(logging.INFO)
    formatter = logging.Formatter()
    handler = logging.StreamHandler()
    handler.setFormatter(formatter)
    logger.addHandler(handler)
    return logger


logger = _init_logger()


def _env_var_to_bool(varname: str, default: bool = False) -> bool:
    """Parse an environment varaible as a boolean."""
    try:
        value = os.environ[varname]
    except KeyError:
        return default

    value_lower = value.lower()
    if value_lower in {"yes", "1", "true"}:
        return True
    elif value_lower in {"no", "0", "false"}:
        return False
    else:
        raise OSError(
            "Failed to parse value of environment variable %s: '%s'" % (varname, value)
        )


class Model:
    """
    Base class wrapping any model to be compiled by femtocrux. Should not be
    instantiated directly. Instead, use one of its child classes like
    :class:`~femtocrux.client.client.FQIRModel` or
    :class:`~femtocrux.client.client.TFLiteModel`.
    """

    def _get_message(self, options: dict = {}) -> cs_pb2.model:
        # Format the options
        options_struct = google.protobuf.struct_pb2.Struct()
        options_struct.update(options)

        # Construct the model with IR
        return cs_pb2.model(**{self._ir_name: self._get_ir()}, options=options_struct)

    @property
    def _ir_name(self) -> str:
        """
        Subclass overrides this to tell which 'ir' field is being returned.
        """
        return NotImplementedError("Subclass must override with IR type.")

    def _get_ir(self) -> Tuple[str, Any]:
        """
        Subclass overrides this to implement the 'ir' field of the model's
        grpc message.
        """
        raise NotImplementedError("Must be defined by subclass")


@dataclass
class FQIRModel(Model):
    """
    Wraps an FQIR model to be compiled by femtocrux.

    :type graph_proto: fmot.fqir.GraphProto, required
    :param graph_proto: The traced FQIR model.

    :type batch_dim: int, optional
    :param batch_dim: The batch dimension to be squeezed from all inputs.

    :type sequence_dim: int, optional
    :param sequence_dim: The sequence dimension to squeezed from all inputs.
    """

    graph_proto: GraphProto = None
    batch_dim: int = None
    sequence_dim: int = None

    @property
    def _ir_name(self) -> str:
        return "fqir"

    def _get_ir(self) -> Any:
        # Serialize FQIR via pickle
        model = pickle.dumps(self.graph_proto)

        # Send the serialized model
        return cs_pb2.fqir(
            model=model,
            batch_dim=self.batch_dim,
            sequence_dim=self.sequence_dim,
        )


@dataclass
class TFLiteModel(Model):
    """
    Wraps a TFLite model to be compiled by femtocrux.

    :type flatbuffer: bytes, required
    :param flatbuffer: The TFLite flatbuffer to be compiled.

    :type signature_name: str, optional
    :param signature_name: The name of the TFLite IO signature to be used for input /
        output metadata. Must be provided if the model contains multiple signatures.
    """

    flatbuffer: bytes = None
    signature_name: str = None

    @property
    def _ir_name(self) -> str:
        return "tflite"

    def _get_ir(self) -> Any:
        return cs_pb2.tflite(model=self.flatbuffer, signature_name=self.signature_name)


class Simulator:
    """
    Simulates a compiled model's behavior on the SPU.
    """

    def __init__(self, client: "CompilerClient", model: Model, options: dict = {}):
        self.client = client
        self.model = model

        # Create an event stream fed by a queue
        self.request_queue = queue.SimpleQueue()
        request_iterator = iter(self.request_queue.get, self._request_sentinel)
        self.response_iterator = client._simulate(request_iterator)

        # Compile the model with the first message
        model_msg = model._get_message(options)
        simulation_start_msg = cs_pb2.simulation_input(model=model_msg)
        self._send_request(simulation_start_msg)

        # Check compilation status
        self._get_response()

    def __del__(self):
        """Close any open streams."""
        self._send_request(self._request_sentinel)

    def _send_request(self, msg):
        self.request_queue.put(msg)

    def _get_response(self):
        response = next(self.response_iterator)
        self.client._check_status(response.status)
        return response

    @property
    def _request_sentinel(self) -> Any:
        """Sentinel value to close the request queue."""
        return None

    def simulate(
        self,
        inputs: Iterable[np.array],
        input_period: float = 0.016,
    ) -> List[np.array]:
        """
        Simulates the model on the given inputs.

        :param inputs: The input tensors in a dictionary of:
            {
                "input_name1": np.ndarray(int16 types ...),
                "input_name2": np.ndarray([int16 types ...])
            }
        :type input_period (float, optional): Duration between each input in a sequence,
            in seconds.

        :rtype: list
        :return: The output tensors.

        """

        simulation_request = cs_pb2.simulation_input(
            data=serialize_sim_inputs_message(inputs, input_period)
        )
        self._send_request(simulation_request)
        response = self._get_response()

        return deserialize_simulation_output(response.outputs), response.report


class CompilerClientImpl:
    """
    Internal implementation of CompilerClient, with extra testing options.

    Allows substituting your own gRPC channel and stub.
    """

    def __init__(self, channel, stub):
        self.channel = channel
        self.stub = stub
        self._check_version()

    def _check_status(self, status):
        """Check a status response, raising an exception if unsuccessful."""
        if not status.success:
            raise RuntimeError(
                "Client received error from compiler server:\n%s" % status.msg
            )

    def _check_version(self):
        """Verify the server's version matches the client."""

        from femtocrux.version import __version__ as client_version

        server_version = self._server_version()
        assert (
            client_version == server_version
        ), """
        Client-server version mismatch:
            client: %s
            server: %s
        """ % (
            client_version,
            server_version,
        )

    def compile(self, model: Model, options: dict = {}) -> bytes:
        """
        Compile the model to a bitstream.

        :type model: Model, required
        :param model: The model to be compiled.

        :type options: dict, optional
        :param options: Complier options.

        :rtype: bytes
        :return: A zip archive of compiler artifacts.
        """

        response = self.stub.compile(model._get_message(options))
        self._check_status(response.status)
        return response.bitfile

    def _ping(self, message: bytes) -> None:
        """Pings the server with a message."""
        response = self.stub.ping(cs_pb2.data(data=message))
        if response.data != message:
            raise RuntimeError("Server response does not match request data!")

    def _simulate(self, in_stream: Iterable) -> Iterable:
        """Calls the 'simulator' bidirectional streaming RPC."""
        return self.stub.simulate(in_stream)

    def simulate(self, model: Model, options: dict = {}) -> Simulator:
        """
        Get a simulator for the model.

        :type model: Model, required
        :param model: The model to be simulated.

        :type options: dict, optional
        :param options: Compiler options.

        :rtype: Simulator
        :return: A simulator for the model.
        """
        return Simulator(client=self, model=model, options=options)

    def get_simulator_object(self, model: Model, options: dict = {}) -> Simulator:
        return self.simulate(model, options)

    def _server_version(self) -> str:
        """Queries the femtocrux version running on the server."""
        response = self.stub.version(google.protobuf.empty_pb2.Empty())
        return response.version


class CompilerClient(CompilerClientImpl):
    """
    Client which spawns and interacts with the compiler server. This is the main
    entrypoint for femtocrux.

    :type docker_kwargs: dict, optional
    :param docker_kwargs: Arguments passed to 'docker run' when the server is spawned.
        This option is recommended for advanced users only. For a list of options, see
        `here <https://docker-py.readthedocs.io/en/stable/containers.html>`_.
        For example, to remove docker's security restrictions, one could use
    .. code-block:: python

            CompilerClient(docker_kwargs={'security_opt': ['seccomp=unconfined']})
    """

    def __init__(self, docker_kwargs: dict[str, Any] = None):
        self.container = None  # For __del__

        # Start a new docker server
        self.container = self._create_docker_server(docker_kwargs)
        self._wait_for_server_ready()
        self._init_network_info(self.container)

        # Establish a connection to the server
        self.channel = self._connect()

        # Initialize the client on this channel
        self.stub = cs_pb2_grpc.CompileStub(self.channel)
        super().__init__(self.channel, self.stub)

    @property
    def status(self):
        if self.container is not None:
            return self.container.status
        else:
            return "exited"

    @property
    def name(self):
        if self.container is not None:
            return self.container.name
        else:
            return None

    def close(self):
        if self.container is not None:
            try:
                self.container.stop()
            except Exception as e:
                logger.info(f"Image already closed... skipping close\n{e}")

    def on_exit(self):
        """Reclaim system resources."""
        if self.container is not None:
            try:
                cli = docker.DockerClient()
                container = cli.containers.get(self.name)
                container.stop()
            except docker.errors.NotFound:
                pass

    def _get_docker_api_client(self):
        """Get a client to the Docker daemon."""
        try:
            return docker.from_env()
        except Exception as exc:
            raise RuntimeError(
                """Failed to connect to the Docker daemon.
                    Please ensure it is installed and running."""
            ) from exc

    def _init_network_info(self, container):
        """
        For local connections only.

        Gets the IP address and port of the container.
        """
        # Get container network settings
        container.reload()
        network_info = container.attrs["NetworkSettings"]

        # Search for the host port bound to loopback
        bound_ports = list(network_info["Ports"].items())
        num_bound_ports = len(bound_ports)
        if num_bound_ports != 1:
            raise OSError(
                "Expected exactly one port to be bound to docker container "
                "'%s'.\nFound %d." % (container.id, num_bound_ports)
            )

        # Extract the port number
        bound_port, bound_sockets = bound_ports[0]
        socket = bound_sockets[0]  # In case of multiple, take the first one
        self.__channel_port__ = socket["HostPort"]

    def _connect(self) -> Any:
        """Establishes a gRPC connection to the server."""

        # Open a gRPC channel to the server
        sock_name = "%s:%s" % (self.channel_addr, self.channel_port)
        channel = grpc.insecure_channel(
            sock_name,
            options=get_channel_options(),
        )
        logger.info("Created gRPC channel at %s" % sock_name)

        # Wait for the channel to be ready
        channel_timeout_seconds = 30
        channel_ready = grpc.channel_ready_future(channel)
        logger.info("Waiting to establish a connection...")
        try:
            channel_ready.result(timeout=channel_timeout_seconds)
        except grpc.FutureTimeoutError as exc:
            raise OSError(
                "Channel timed out after %s seconds. Check that the server is running."
                % channel_timeout_seconds
            ) from exc
        logger.info("Connection successful.")

        return channel

    @property
    def channel_addr(self) -> str:
        """
        IP address used for the gRPC channel.

        Note that '0.0.0.0' does NOT work on Windows hosts.
        """
        return "localhost"

    @property
    def channel_port(self) -> int:
        """
        Port used for the gRPC channel.
        """
        return self.__channel_port__

    @property
    def _container_port(self) -> int:
        """Port used inside the container."""
        return 50051

    @property
    def _container_label(self) -> str:
        """Label attached to identify containers started by this client."""
        return "femtocrux_server"

    def _get_unused_container_name(self) -> str:
        """Get an unused container name."""

        # Search for an unused name
        client = self._get_docker_api_client()
        container_idx = 0
        while True:
            name = "femtocrux_server_%d" % container_idx
            try:
                client.containers.get(name)
            except docker.errors.NotFound:
                # If no collision, use this name
                return name

            container_idx += 1

    def _pull_docker_image(self):
        """Pull the Docker image from remote."""

        logger.info(
            """
            Attempting to pull docker image from remote.

            Alternatively, you can pull the image yourself with the command:
                docker pull %s
            """,
            __docker_image_name__,
        )

        # Log in to Github
        client = self._get_docker_api_client()
        while True:
            # Get the password
            manual_pass = True
            if "GH_PACKAGE_KEY" in os.environ:
                password = os.environ["GH_PACKAGE_KEY"]
                manual_pass = False
            else:
                # Prompt the user for password entry
                password = getpass("Please enter your Femtosense-provided key:")

            # Log in to the client
            try:
                resp = client.login(
                    "femtodaemon", password, registry="https://" + __docker_registry__
                )
            except docker.errors.APIError as exc:
                if "denied" in exc.explanation:
                    logger.error("Docker authetication failed.")
                    # Retry password entry
                    if manual_pass:
                        continue

                raise RuntimeError("Docker authentication failed") from exc

            # Login successful
            logger.info(resp.get("Status", ""))
            break

        def image_not_found_error() -> RuntimeError:
            """Return an exception saying the image wasn't found."""
            return RuntimeError(
                """Docker image not found:
                %s
            Please notify your Femtosense representative."""
                % (__docker_image_name__)
            )

        # Download the image
        logger.info("Downloading image. This could take a few minutes...")
        try:
            client.images.pull(__docker_image_name__)
        except docker.errors.ImageNotFound as exc:
            raise image_not_found_error() from exc
        except docker.errors.APIError as exc:
            if exc.explanation == "manifest unknown":
                logger.error(
                    "Docker image %s not found on the remote. Check if it is "
                    "published.",
                    __docker_image_name__,
                )
            raise image_not_found_error() from exc

        logger.info("Download completed.")

    def _create_docker_server(
        self, docker_kwargs: dict[str, Any] = None
    ) -> docker.models.containers.Container:
        """
        Starts the server in a new Docker container.
        """
        if docker_kwargs is None:
            docker_kwargs = {}

        # Get a client for the Docker daemon
        client = self._get_docker_api_client()

        # Pull the image, if not available
        existing_image_names = [
            tag for image in client.images.list() for tag in image.tags
        ]
        if __docker_image_name__ not in existing_image_names:
            # Check if we are allowed to pull the image.
            # This is disabled for CI builds.
            image_not_found_msg = (
                "Failed to find the docker image %s locally." % __docker_image_name__
            )
            if not _env_var_to_bool("FS_ALLOW_DOCKER_PULL", default=True):
                raise RuntimeError(
                    """
                    %s
                    Docker pull is disabled by the environment.
                    """
                    % image_not_found_msg
                )

            # Pull the image from remote
            logger.info(image_not_found_msg)
            self._pull_docker_image()

        # Bind a random port on the host to the container's gRPC port
        port_interface = {self._container_port: None}
        command = "--port %s" % self._container_port

        # Start a container running the server
        container = client.containers.run(
            __docker_image_name__,
            command=command,  # Appends entrypoint with args
            detach=True,
            labels=[self._container_label],
            stderr=True,
            stdout=True,
            ports=port_interface,
            name=self._get_unused_container_name(),
            auto_remove=True,
            **docker_kwargs,
        )

        return container

    def _wait_for_server_ready(self):
        """
        Block until the Docker container is ready to handle requests.
        """

        container = self.container

        # Block until the container starts
        num_attempts = 5
        wait_interval = 1.0  # Seconds
        print("Checking container status...")
        for attempt in range(num_attempts):
            container.reload()
            status = container.status
            if status == "created":
                # Sleep and try again
                print("Container starting up. Retrying in %fs..." % wait_interval)
                time.sleep(wait_interval)
                continue
            elif status == "running":
                print("Container started successfully.")
                break
            elif status == "exited":
                raise RuntimeError("Container exited! See logs:\n%d" % container.logs())
            else:
                raise RuntimeError("Unrecognized docker container status: %d" % status)

        # Check the final status
        container.reload()
        if container.status != "running":
            raise RuntimeError(
                "Container failed to start after %d attempts" % num_attempts
            )

        # Check the container's health
        for attempt in range(num_attempts):
            exit_code, output = container.exec_run(
                "python3 /femtocrux/femtocrux/server/healthcheck.py"
            )

            if exit_code == 0:
                print("Container passed health check.")
                break

            time.sleep(wait_interval)

        # Check the last return code
        if exit_code != 0:
            raise RuntimeError(
                "Docker container failed %d health check(s)!\nLast output:\n%s"
                % (num_attempts, output.decode("utf-8"))
            )


@contextmanager
def ManagedCompilerClient(docker_kwargs: dict[str, Any] = None) -> CompilerClient:
    client = CompilerClient(docker_kwargs=docker_kwargs)
    try:
        yield client
    finally:
        client.close()


if __name__ == "__main__":
    logging.basicConfig(stream=sys.stdout, level=logging.INFO)
    client = CompilerClient()
    logger.info("Client started successfully.")
