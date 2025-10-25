"""
ECS Service Configuration
Maintainers: Eric Wilson
MIT License. See Project Root for the license information.
"""

from typing import Dict, Any, List, Optional


class EcsServiceConfig:
    """ECS Service Configuration"""

    def __init__(self, config: Dict[str, Any]) -> None:
        self._config = config

    @property
    def name(self) -> str:
        """Service name"""
        return self._config.get("name", "")

    @property
    def cluster_name(self) -> Optional[str]:
        """ECS Cluster name"""
        return self._config.get("cluster_name")

    @property
    def task_definition(self) -> Dict[str, Any]:
        """Task definition configuration"""
        return self._config.get("task_definition", {})

    @property
    def container_definitions(self) -> List[Dict[str, Any]]:
        """Container definitions"""
        return self.task_definition.get("containers", [])

    @property
    def cpu(self) -> str:
        """Task CPU units"""
        return self.task_definition.get("cpu", "256")

    @property
    def memory(self) -> str:
        """Task memory (MB)"""
        return self.task_definition.get("memory", "512")

    @property
    def launch_type(self) -> str:
        """Launch type: FARGATE or EC2"""
        return self._config.get("launch_type", "FARGATE")

    @property
    def desired_count(self) -> int:
        """Desired number of tasks"""
        return self._config.get("desired_count", 2)

    @property
    def min_capacity(self) -> int:
        """Minimum number of tasks"""
        return self._config.get("min_capacity", 1)

    @property
    def max_capacity(self) -> int:
        """Maximum number of tasks"""
        return self._config.get("max_capacity", 4)

    @property
    def vpc_id(self) -> Optional[str]:
        """VPC ID"""
        return self._config.get("vpc_id")

    @property
    def subnet_group_name(self) -> Optional[str]:
        """Subnet group name for service placement"""
        return self._config.get("subnet_group_name")

    @property
    def security_group_ids(self) -> List[str]:
        """Security group IDs"""
        return self._config.get("security_group_ids", [])

    @property
    def assign_public_ip(self) -> bool:
        """Whether to assign public IP addresses"""
        return self._config.get("assign_public_ip", False)

    @property
    def target_group_arns(self) -> List[str]:
        """Target group ARNs for load balancing"""
        return self._config.get("target_group_arns", [])

    @property
    def container_port(self) -> int:
        """Container port for load balancer"""
        return self._config.get("container_port", 80)

    @property
    def health_check_grace_period(self) -> int:
        """Health check grace period in seconds"""
        return self._config.get("health_check_grace_period", 60)

    @property
    def enable_execute_command(self) -> bool:
        """Enable ECS Exec for debugging"""
        return self._config.get("enable_execute_command", False)

    @property
    def enable_auto_scaling(self) -> bool:
        """Enable auto-scaling"""
        return self._config.get("enable_auto_scaling", True)

    @property
    def auto_scaling_target_cpu(self) -> int:
        """Target CPU utilization percentage for auto-scaling"""
        return self._config.get("auto_scaling_target_cpu", 70)

    @property
    def auto_scaling_target_memory(self) -> int:
        """Target memory utilization percentage for auto-scaling"""
        return self._config.get("auto_scaling_target_memory", 80)

    @property
    def tags(self) -> Dict[str, str]:
        """Resource tags"""
        return self._config.get("tags", {})

    @property
    def ssm_exports(self) -> Dict[str, str]:
        """SSM parameter exports"""
        return self._config.get("ssm_exports", {})

    @property
    def ssm_imports(self) -> Dict[str, str]:
        """SSM parameter imports"""
        return self._config.get("ssm_imports", {})

    @property
    def deployment_type(self) -> str:
        """Deployment type: production, maintenance, or blue-green"""
        return self._config.get("deployment_type", "production")

    @property
    def is_maintenance_mode(self) -> bool:
        """Whether this is a maintenance mode deployment"""
        return self.deployment_type == "maintenance"

    @property
    def volumes(self) -> List[Dict[str, Any]]:
        """
        Volume definitions for the task.
        Supports host volumes for EC2 launch type and EFS volumes.
        Each volume should have:
        - name: volume name
        - host: {source_path: "/path/on/host"} for bind mounts
        - efs: {...} for EFS volumes
        """
        return self.task_definition.get("volumes", [])
