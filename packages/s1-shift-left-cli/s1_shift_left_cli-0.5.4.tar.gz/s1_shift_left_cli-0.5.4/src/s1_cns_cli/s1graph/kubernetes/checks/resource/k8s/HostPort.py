from typing import Any, Dict

from s1_cns_cli.s1graph.common.models.enums import CheckResult
from s1_cns_cli.s1graph.kubernetes.checks.resource.base_container_check import BaseK8sContainerCheck


class HostPort(BaseK8sContainerCheck):
    def __init__(self) -> None:
        """
        https://kubernetes.io/docs/concepts/configuration/overview/

        Don’t specify a hostPort for a Pod unless it is absolutely necessary.
        When you bind a Pod to a hostPort, it limits the number of places the
        Pod can be scheduled, because each <hostIP, hostPort, protocol> combination
        must be unique.
        """
        name = "Do not specify hostPort unless absolutely necessary"
        id = "CKV_K8S_26"
        # Location: container .ports[].hostPort
        super().__init__(name=name, id=id)

    def scan_container_conf(self, metadata: Dict[str, Any], conf: Dict[str, Any]) -> CheckResult:
        if conf.get("ports"):
            for idx, port in enumerate(conf["ports"]):
                if "hostPort" in port:
                    self.evaluated_container_keys = [f"ports/[{idx}]/hostPort"]
                    return CheckResult.FAILED
        return CheckResult.PASSED


check = HostPort()
