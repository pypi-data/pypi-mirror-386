import argparse
from copy import deepcopy
import os
import webbrowser
from http import HTTPStatus
import time
from subprocess import Popen, PIPE
from functools import partial

from pyntcli.commands.util import build_scan_details_url
from pyntcli.pynt_docker import pynt_container
from pyntcli.ui import ui_thread
from pyntcli.commands import util, sub_command
from pyntcli.transport import pynt_requests


def command_usage():
    return (
        ui_thread.PrinterText(
            "Command integration to Pynt. Run a security scan with a given command."
        )
        .with_line("")
        .with_line("Usage:", style=ui_thread.PrinterText.HEADER)
        .with_line("\tpynt command [OPTIONS]")
        .with_line("")
        .with_line("Options:", style=ui_thread.PrinterText.HEADER)
        .with_line("\t--cmd - The command that runs the functional tests")
        .with_line('\t--captured-domains - Pynt will scan only these domains and subdomains. For all domains write "*"')
        .with_line('\t--test-name - A name for your Pynt scan')
        .with_line("\t--port - Set the port pynt will listen to (DEFAULT: random)")
        .with_line("\t--allow-errors - If present will allow command to fail and continue execution")
        .with_line("\t--ca-path - The path to the CA file in PEM format")
        .with_line("\t--proxy-port - Set the port proxied traffic should be routed to (DEFAULT: 6666)")
        .with_line("\t--report - If present will save the generated report in this path.")
        .with_line("\t--insecure - Use when target uses self signed certificates")
        .with_line("\t--self-signed - Use when the functional test verify SSL")
        .with_line("\t--no-proxy-export - Pynt will not export the proxy settings to the environment")
        .with_line("\t--application-id - Attach the scan to an application, you can find the ID in your applications area at app.pynt.io")
        .with_line(
            "\t--application-name - Attach the scan to an application, application will be created automatically if it does not exist.")
        .with_line("\t--host-ca - Path to the CA file in PEM format to enable SSL certificate verification for pynt when running through a VPN.")
        .with_line("\t--severity-level - 'all', 'medium', 'high', 'critical', 'none' (default) ")
        .with_line("\t--tag - Tag the scan. Repeat for multiple tags")
        .with_line("\t--verbose - Use to get more detailed information about the run")
    )


class CommandSubCommand(sub_command.PyntSubCommand):
    def __init__(self, name) -> None:
        super().__init__(name)

    def print_usage(self, *args):
        ui_thread.print(command_usage())

    def add_cmd(self, parent: argparse._SubParsersAction) -> argparse.ArgumentParser:
        proxy_cmd = parent.add_parser(self.name)
        proxy_cmd.add_argument("--port", "-p", help="", type=int, default=util.find_open_port())
        proxy_cmd.add_argument("--proxy-port", help="", type=int, default=6666)
        proxy_cmd.add_argument("--cmd", help="", default="", required=True)
        proxy_cmd.add_argument("--captured-domains", nargs="+", help="", default="", required=False)
        proxy_cmd.add_argument("--test-name", help="", default="", required=False)
        proxy_cmd.add_argument("--allow-errors", action="store_true")
        proxy_cmd.add_argument("--no-proxy-export", action="store_true")
        proxy_cmd.add_argument("--ca-path", type=str, default="")
        proxy_cmd.add_argument("--self-signed", action="store_true")
        proxy_cmd.add_argument("--report", type=str, default="")
        proxy_cmd.add_argument("--severity-level", choices=["all", "medium", "high", "critical", "none"], default="none")
        proxy_cmd.print_usage = self.print_usage
        proxy_cmd.print_help = self.print_usage
        return proxy_cmd

    def _updated_environment(self, args):
        env_copy = deepcopy(os.environ)
        env_copy.update(
            {
                "RUNNING_FROM_PYNT": "True",
            }
        )
        if "self_signed" in args and args.self_signed:
            cert_path = os.path.join(os.path.expanduser('~'), '.pynt', 'cert')
            cert_file_path = os.path.join(cert_path, 'mitmproxy-ca-cert.pem')
            env_copy.update(
                {
                    "REQUESTS_CA_BUNDLE": cert_file_path,
                    "SSL_CERT_FILE": cert_file_path,
                    "NODE_EXTRA_CA_CERTS": cert_file_path
                }
            )
        if "no_proxy_export" in args and args.no_proxy_export:
            return env_copy
        else:
            env_copy.update(
                {
                    "http_proxy": "http://localhost:{}".format(args.proxy_port),
                    "https_proxy": "http://localhost:{}".format(args.proxy_port),
                    "JAVA_TOOL_OPTIONS": "-Dhttp.proxyHost=localhost -Dhttp.proxyPort={} -Dhttps.proxyHost=localhost -Dhttps.proxyPort={}".format(args.proxy_port, args.proxy_port),
                }
            )
            return env_copy

    def _start_proxy(self, args):
        res = pynt_requests.put(
            self.proxy_server_base_url.format(args.port) + "/proxy/start"
        )
        res.raise_for_status()
        self.scan_id = res.json()["scanId"]

    def _stop_proxy(self, args):
        start = time.time()
        while start + self.proxy_healthcheck_buffer > time.time():
            res = pynt_requests.put(
                self.proxy_server_base_url.format(args.port) + "/proxy/stop",
                json={"scanId": self.scan_id},
            )
            if res.status_code == HTTPStatus.OK:
                return
            time.sleep(self.proxy_sleep_interval)
        raise TimeoutError()


    def run_cmd(self, args: argparse.Namespace):
        container_config = pynt_container.DockerContainerConfig(
            args,
            "proxy",
            pynt_container.api_port(args.port),
            pynt_container.proxy_port(args.proxy_port),
        )

        if args.captured_domains:
            for host in args.captured_domains:
                container_config.docker_arguments += ["--host-targets", host]

        if args.test_name:
            container_config.docker_arguments += ["--test-name", args.test_name]

        if "ca_path" in args and args.ca_path:
            if not os.path.isfile(args.ca_path):
                ui_thread.print(
                    ui_thread.PrinterText(
                        "Could not find the provided ca path, please provide with a valid path",
                        ui_thread.PrinterText.WARNING,
                    )
                )
                return

            ca_name = os.path.basename(args.ca_path)
            container_config.docker_arguments += ["--ca-path", ca_name]
            container_config.mounts.append(
                pynt_container.create_mount(
                    os.path.abspath(args.ca_path), "/etc/pynt/{}".format(ca_name)
                )
            )

        proxy_docker = pynt_container.PyntContainerNative(container_config)

        proxy_docker.prepare_client()
        proxy_docker.pre_run_validation(args.port)
        proxy_docker.run()

        ui_thread.print_generator(proxy_docker.stdout)

        util.wait_for_healthcheck("http://localhost:{}".format(args.port))
        ui_thread.print_verbose(util.GOT_INITIAL_HEALTHCHECK_MESSAGE)
        ui_thread.print(ui_thread.PrinterText(
            "Pynt docker is ready",
            ui_thread.PrinterText.INFO,
        ))

        if args.captured_domains:
            ui_thread.print(
                "\nWill scan APIs that belong to {} domains only".format(
                    args.captured_domains
                )
            )

        self._start_proxy(args)

        user_process = Popen(
            args.cmd,
            shell=True,
            stdout=PIPE,
            stderr=PIPE,
            env=self._updated_environment(args),
        )
        ui_thread.print_generator(user_process.stdout)
        ui_thread.print_generator(user_process.stderr)
        rc = user_process.wait()
        if rc != 0 and not args.allow_errors:
            proxy_docker.stop()
            ui_thread.print(
                ui_thread.PrinterText(
                    "The Command you provided finished with error return code {}, If you wish Pynt to run anyway, run with --allow-errors".format(
                        rc
                    )
                )
            )
            return

        self._stop_proxy(args)

        with ui_thread.progress(
                "ws://localhost:{}/progress?scanId={}".format(args.port, self.scan_id),
                partial(lambda *args: None),
                "scan in progress...",
                100,
        ):
            app_id = self.get_app_id(args.port, self.scan_id)
            scan_details_url = build_scan_details_url(self.scan_id, app_id)
            html_report_path = self.handle_html_report(args) # this also indicates that the scan is done

        if scan_details_url:
            webbrowser.open(scan_details_url)
        else:
            webbrowser.open("file://{}".format(html_report_path))

        self.handle_json_report(args)
