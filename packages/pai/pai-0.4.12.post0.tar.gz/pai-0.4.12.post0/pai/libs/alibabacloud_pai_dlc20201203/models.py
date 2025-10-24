# -*- coding: utf-8 -*-
# This file is auto-generated, don't edit it. Thanks.
from Tea.model import TeaModel
from typing import Dict, List


class AliyunAccounts(TeaModel):
    def __init__(
        self,
        aliyun_uid: str = None,
        employee_id: str = None,
        gmt_create_time: str = None,
        gmt_modify_time: str = None,
    ):
        self.aliyun_uid = aliyun_uid
        self.employee_id = employee_id
        self.gmt_create_time = gmt_create_time
        self.gmt_modify_time = gmt_modify_time

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.aliyun_uid is not None:
            result['AliyunUid'] = self.aliyun_uid
        if self.employee_id is not None:
            result['EmployeeId'] = self.employee_id
        if self.gmt_create_time is not None:
            result['GmtCreateTime'] = self.gmt_create_time
        if self.gmt_modify_time is not None:
            result['GmtModifyTime'] = self.gmt_modify_time
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('AliyunUid') is not None:
            self.aliyun_uid = m.get('AliyunUid')
        if m.get('EmployeeId') is not None:
            self.employee_id = m.get('EmployeeId')
        if m.get('GmtCreateTime') is not None:
            self.gmt_create_time = m.get('GmtCreateTime')
        if m.get('GmtModifyTime') is not None:
            self.gmt_modify_time = m.get('GmtModifyTime')
        return self


class CodeSourceItem(TeaModel):
    def __init__(
        self,
        code_branch: str = None,
        code_commit: str = None,
        code_repo: str = None,
        code_repo_access_token: str = None,
        code_repo_user_name: str = None,
        code_source_id: str = None,
        description: str = None,
        display_name: str = None,
        gmt_create_time: str = None,
        gmt_modify_time: str = None,
        user_id: str = None,
    ):
        self.code_branch = code_branch
        self.code_commit = code_commit
        self.code_repo = code_repo
        self.code_repo_access_token = code_repo_access_token
        self.code_repo_user_name = code_repo_user_name
        self.code_source_id = code_source_id
        self.description = description
        self.display_name = display_name
        self.gmt_create_time = gmt_create_time
        self.gmt_modify_time = gmt_modify_time
        self.user_id = user_id

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.code_branch is not None:
            result['CodeBranch'] = self.code_branch
        if self.code_commit is not None:
            result['CodeCommit'] = self.code_commit
        if self.code_repo is not None:
            result['CodeRepo'] = self.code_repo
        if self.code_repo_access_token is not None:
            result['CodeRepoAccessToken'] = self.code_repo_access_token
        if self.code_repo_user_name is not None:
            result['CodeRepoUserName'] = self.code_repo_user_name
        if self.code_source_id is not None:
            result['CodeSourceId'] = self.code_source_id
        if self.description is not None:
            result['Description'] = self.description
        if self.display_name is not None:
            result['DisplayName'] = self.display_name
        if self.gmt_create_time is not None:
            result['GmtCreateTime'] = self.gmt_create_time
        if self.gmt_modify_time is not None:
            result['GmtModifyTime'] = self.gmt_modify_time
        if self.user_id is not None:
            result['UserId'] = self.user_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('CodeBranch') is not None:
            self.code_branch = m.get('CodeBranch')
        if m.get('CodeCommit') is not None:
            self.code_commit = m.get('CodeCommit')
        if m.get('CodeRepo') is not None:
            self.code_repo = m.get('CodeRepo')
        if m.get('CodeRepoAccessToken') is not None:
            self.code_repo_access_token = m.get('CodeRepoAccessToken')
        if m.get('CodeRepoUserName') is not None:
            self.code_repo_user_name = m.get('CodeRepoUserName')
        if m.get('CodeSourceId') is not None:
            self.code_source_id = m.get('CodeSourceId')
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('DisplayName') is not None:
            self.display_name = m.get('DisplayName')
        if m.get('GmtCreateTime') is not None:
            self.gmt_create_time = m.get('GmtCreateTime')
        if m.get('GmtModifyTime') is not None:
            self.gmt_modify_time = m.get('GmtModifyTime')
        if m.get('UserId') is not None:
            self.user_id = m.get('UserId')
        return self


class EnvVar(TeaModel):
    def __init__(
        self,
        name: str = None,
        value: str = None,
    ):
        self.name = name
        self.value = value

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.name is not None:
            result['Name'] = self.name
        if self.value is not None:
            result['Value'] = self.value
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('Name') is not None:
            self.name = m.get('Name')
        if m.get('Value') is not None:
            self.value = m.get('Value')
        return self


class ResourceRequirements(TeaModel):
    def __init__(
        self,
        limits: Dict[str, str] = None,
        requests: Dict[str, str] = None,
    ):
        self.limits = limits
        self.requests = requests

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.limits is not None:
            result['Limits'] = self.limits
        if self.requests is not None:
            result['Requests'] = self.requests
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('Limits') is not None:
            self.limits = m.get('Limits')
        if m.get('Requests') is not None:
            self.requests = m.get('Requests')
        return self


class ContainerSpec(TeaModel):
    def __init__(
        self,
        args: List[str] = None,
        command: List[str] = None,
        env: List[EnvVar] = None,
        image: str = None,
        name: str = None,
        resources: ResourceRequirements = None,
        working_dir: str = None,
    ):
        self.args = args
        self.command = command
        self.env = env
        self.image = image
        self.name = name
        self.resources = resources
        self.working_dir = working_dir

    def validate(self):
        if self.env:
            for k in self.env:
                if k:
                    k.validate()
        if self.resources:
            self.resources.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.args is not None:
            result['Args'] = self.args
        if self.command is not None:
            result['Command'] = self.command
        result['Env'] = []
        if self.env is not None:
            for k in self.env:
                result['Env'].append(k.to_map() if k else None)
        if self.image is not None:
            result['Image'] = self.image
        if self.name is not None:
            result['Name'] = self.name
        if self.resources is not None:
            result['Resources'] = self.resources.to_map()
        if self.working_dir is not None:
            result['WorkingDir'] = self.working_dir
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('Args') is not None:
            self.args = m.get('Args')
        if m.get('Command') is not None:
            self.command = m.get('Command')
        self.env = []
        if m.get('Env') is not None:
            for k in m.get('Env'):
                temp_model = EnvVar()
                self.env.append(temp_model.from_map(k))
        if m.get('Image') is not None:
            self.image = m.get('Image')
        if m.get('Name') is not None:
            self.name = m.get('Name')
        if m.get('Resources') is not None:
            temp_model = ResourceRequirements()
            self.resources = temp_model.from_map(m['Resources'])
        if m.get('WorkingDir') is not None:
            self.working_dir = m.get('WorkingDir')
        return self


class DataSourceItem(TeaModel):
    def __init__(
        self,
        data_source_id: str = None,
        data_source_type: str = None,
        description: str = None,
        display_name: str = None,
        endpoint: str = None,
        file_system_id: str = None,
        gmt_create_time: str = None,
        gmt_modify_time: str = None,
        mount_path: str = None,
        options: str = None,
        path: str = None,
        user_id: str = None,
    ):
        self.data_source_id = data_source_id
        self.data_source_type = data_source_type
        self.description = description
        self.display_name = display_name
        self.endpoint = endpoint
        self.file_system_id = file_system_id
        self.gmt_create_time = gmt_create_time
        self.gmt_modify_time = gmt_modify_time
        self.mount_path = mount_path
        self.options = options
        self.path = path
        self.user_id = user_id

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.data_source_id is not None:
            result['DataSourceId'] = self.data_source_id
        if self.data_source_type is not None:
            result['DataSourceType'] = self.data_source_type
        if self.description is not None:
            result['Description'] = self.description
        if self.display_name is not None:
            result['DisplayName'] = self.display_name
        if self.endpoint is not None:
            result['Endpoint'] = self.endpoint
        if self.file_system_id is not None:
            result['FileSystemId'] = self.file_system_id
        if self.gmt_create_time is not None:
            result['GmtCreateTime'] = self.gmt_create_time
        if self.gmt_modify_time is not None:
            result['GmtModifyTime'] = self.gmt_modify_time
        if self.mount_path is not None:
            result['MountPath'] = self.mount_path
        if self.options is not None:
            result['Options'] = self.options
        if self.path is not None:
            result['Path'] = self.path
        if self.user_id is not None:
            result['UserId'] = self.user_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('DataSourceId') is not None:
            self.data_source_id = m.get('DataSourceId')
        if m.get('DataSourceType') is not None:
            self.data_source_type = m.get('DataSourceType')
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('DisplayName') is not None:
            self.display_name = m.get('DisplayName')
        if m.get('Endpoint') is not None:
            self.endpoint = m.get('Endpoint')
        if m.get('FileSystemId') is not None:
            self.file_system_id = m.get('FileSystemId')
        if m.get('GmtCreateTime') is not None:
            self.gmt_create_time = m.get('GmtCreateTime')
        if m.get('GmtModifyTime') is not None:
            self.gmt_modify_time = m.get('GmtModifyTime')
        if m.get('MountPath') is not None:
            self.mount_path = m.get('MountPath')
        if m.get('Options') is not None:
            self.options = m.get('Options')
        if m.get('Path') is not None:
            self.path = m.get('Path')
        if m.get('UserId') is not None:
            self.user_id = m.get('UserId')
        return self


class DebuggerConfig(TeaModel):
    def __init__(
        self,
        content: str = None,
        debugger_config_id: str = None,
        description: str = None,
        display_name: str = None,
        gmt_create_time: str = None,
        gmt_modify_time: str = None,
    ):
        self.content = content
        self.debugger_config_id = debugger_config_id
        self.description = description
        self.display_name = display_name
        self.gmt_create_time = gmt_create_time
        self.gmt_modify_time = gmt_modify_time

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.content is not None:
            result['Content'] = self.content
        if self.debugger_config_id is not None:
            result['DebuggerConfigId'] = self.debugger_config_id
        if self.description is not None:
            result['Description'] = self.description
        if self.display_name is not None:
            result['DisplayName'] = self.display_name
        if self.gmt_create_time is not None:
            result['GmtCreateTime'] = self.gmt_create_time
        if self.gmt_modify_time is not None:
            result['GmtModifyTime'] = self.gmt_modify_time
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('Content') is not None:
            self.content = m.get('Content')
        if m.get('DebuggerConfigId') is not None:
            self.debugger_config_id = m.get('DebuggerConfigId')
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('DisplayName') is not None:
            self.display_name = m.get('DisplayName')
        if m.get('GmtCreateTime') is not None:
            self.gmt_create_time = m.get('GmtCreateTime')
        if m.get('GmtModifyTime') is not None:
            self.gmt_modify_time = m.get('GmtModifyTime')
        return self


class DebuggerJob(TeaModel):
    def __init__(
        self,
        debugger_job_id: str = None,
        display_name: str = None,
        duration: str = None,
        gmt_create_time: str = None,
        gmt_failed_time: str = None,
        gmt_finish_time: str = None,
        gmt_running_time: str = None,
        gmt_stopped_time: str = None,
        gmt_submitted_time: str = None,
        gmt_succeed_time: str = None,
        status: str = None,
        user_id: str = None,
        workspace_id: str = None,
        workspace_name: str = None,
    ):
        self.debugger_job_id = debugger_job_id
        self.display_name = display_name
        self.duration = duration
        self.gmt_create_time = gmt_create_time
        self.gmt_failed_time = gmt_failed_time
        self.gmt_finish_time = gmt_finish_time
        self.gmt_running_time = gmt_running_time
        self.gmt_stopped_time = gmt_stopped_time
        self.gmt_submitted_time = gmt_submitted_time
        self.gmt_succeed_time = gmt_succeed_time
        self.status = status
        self.user_id = user_id
        self.workspace_id = workspace_id
        self.workspace_name = workspace_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.debugger_job_id is not None:
            result['DebuggerJobId'] = self.debugger_job_id
        if self.display_name is not None:
            result['DisplayName'] = self.display_name
        if self.duration is not None:
            result['Duration'] = self.duration
        if self.gmt_create_time is not None:
            result['GmtCreateTime'] = self.gmt_create_time
        if self.gmt_failed_time is not None:
            result['GmtFailedTime'] = self.gmt_failed_time
        if self.gmt_finish_time is not None:
            result['GmtFinishTime'] = self.gmt_finish_time
        if self.gmt_running_time is not None:
            result['GmtRunningTime'] = self.gmt_running_time
        if self.gmt_stopped_time is not None:
            result['GmtStoppedTime'] = self.gmt_stopped_time
        if self.gmt_submitted_time is not None:
            result['GmtSubmittedTime'] = self.gmt_submitted_time
        if self.gmt_succeed_time is not None:
            result['GmtSucceedTime'] = self.gmt_succeed_time
        if self.status is not None:
            result['Status'] = self.status
        if self.user_id is not None:
            result['UserId'] = self.user_id
        if self.workspace_id is not None:
            result['WorkspaceId'] = self.workspace_id
        if self.workspace_name is not None:
            result['WorkspaceName'] = self.workspace_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('DebuggerJobId') is not None:
            self.debugger_job_id = m.get('DebuggerJobId')
        if m.get('DisplayName') is not None:
            self.display_name = m.get('DisplayName')
        if m.get('Duration') is not None:
            self.duration = m.get('Duration')
        if m.get('GmtCreateTime') is not None:
            self.gmt_create_time = m.get('GmtCreateTime')
        if m.get('GmtFailedTime') is not None:
            self.gmt_failed_time = m.get('GmtFailedTime')
        if m.get('GmtFinishTime') is not None:
            self.gmt_finish_time = m.get('GmtFinishTime')
        if m.get('GmtRunningTime') is not None:
            self.gmt_running_time = m.get('GmtRunningTime')
        if m.get('GmtStoppedTime') is not None:
            self.gmt_stopped_time = m.get('GmtStoppedTime')
        if m.get('GmtSubmittedTime') is not None:
            self.gmt_submitted_time = m.get('GmtSubmittedTime')
        if m.get('GmtSucceedTime') is not None:
            self.gmt_succeed_time = m.get('GmtSucceedTime')
        if m.get('Status') is not None:
            self.status = m.get('Status')
        if m.get('UserId') is not None:
            self.user_id = m.get('UserId')
        if m.get('WorkspaceId') is not None:
            self.workspace_id = m.get('WorkspaceId')
        if m.get('WorkspaceName') is not None:
            self.workspace_name = m.get('WorkspaceName')
        return self


class DebuggerJobIssue(TeaModel):
    def __init__(
        self,
        debugger_job_issue: str = None,
        gmt_create_time: str = None,
        job_debugger_issue_id: str = None,
        job_id: str = None,
        reason_code: str = None,
        reason_message: str = None,
        rule_name: str = None,
    ):
        self.debugger_job_issue = debugger_job_issue
        self.gmt_create_time = gmt_create_time
        self.job_debugger_issue_id = job_debugger_issue_id
        self.job_id = job_id
        self.reason_code = reason_code
        self.reason_message = reason_message
        self.rule_name = rule_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.debugger_job_issue is not None:
            result['DebuggerJobIssue'] = self.debugger_job_issue
        if self.gmt_create_time is not None:
            result['GmtCreateTime'] = self.gmt_create_time
        if self.job_debugger_issue_id is not None:
            result['JobDebuggerIssueId'] = self.job_debugger_issue_id
        if self.job_id is not None:
            result['JobId'] = self.job_id
        if self.reason_code is not None:
            result['ReasonCode'] = self.reason_code
        if self.reason_message is not None:
            result['ReasonMessage'] = self.reason_message
        if self.rule_name is not None:
            result['RuleName'] = self.rule_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('DebuggerJobIssue') is not None:
            self.debugger_job_issue = m.get('DebuggerJobIssue')
        if m.get('GmtCreateTime') is not None:
            self.gmt_create_time = m.get('GmtCreateTime')
        if m.get('JobDebuggerIssueId') is not None:
            self.job_debugger_issue_id = m.get('JobDebuggerIssueId')
        if m.get('JobId') is not None:
            self.job_id = m.get('JobId')
        if m.get('ReasonCode') is not None:
            self.reason_code = m.get('ReasonCode')
        if m.get('ReasonMessage') is not None:
            self.reason_message = m.get('ReasonMessage')
        if m.get('RuleName') is not None:
            self.rule_name = m.get('RuleName')
        return self


class DebuggerResult(TeaModel):
    def __init__(
        self,
        debugger_config_content: str = None,
        debugger_job_issues: str = None,
        debugger_job_status: str = None,
        debugger_report_url: str = None,
        job_display_name: str = None,
        job_id: str = None,
        job_user_id: str = None,
    ):
        self.debugger_config_content = debugger_config_content
        self.debugger_job_issues = debugger_job_issues
        self.debugger_job_status = debugger_job_status
        self.debugger_report_url = debugger_report_url
        self.job_display_name = job_display_name
        self.job_id = job_id
        self.job_user_id = job_user_id

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.debugger_config_content is not None:
            result['DebuggerConfigContent'] = self.debugger_config_content
        if self.debugger_job_issues is not None:
            result['DebuggerJobIssues'] = self.debugger_job_issues
        if self.debugger_job_status is not None:
            result['DebuggerJobStatus'] = self.debugger_job_status
        if self.debugger_report_url is not None:
            result['DebuggerReportURL'] = self.debugger_report_url
        if self.job_display_name is not None:
            result['JobDisplayName'] = self.job_display_name
        if self.job_id is not None:
            result['JobId'] = self.job_id
        if self.job_user_id is not None:
            result['JobUserId'] = self.job_user_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('DebuggerConfigContent') is not None:
            self.debugger_config_content = m.get('DebuggerConfigContent')
        if m.get('DebuggerJobIssues') is not None:
            self.debugger_job_issues = m.get('DebuggerJobIssues')
        if m.get('DebuggerJobStatus') is not None:
            self.debugger_job_status = m.get('DebuggerJobStatus')
        if m.get('DebuggerReportURL') is not None:
            self.debugger_report_url = m.get('DebuggerReportURL')
        if m.get('JobDisplayName') is not None:
            self.job_display_name = m.get('JobDisplayName')
        if m.get('JobId') is not None:
            self.job_id = m.get('JobId')
        if m.get('JobUserId') is not None:
            self.job_user_id = m.get('JobUserId')
        return self


class EcsSpec(TeaModel):
    def __init__(
        self,
        accelerator_type: str = None,
        cpu: int = None,
        gpu: int = None,
        gpu_type: str = None,
        instance_type: str = None,
        is_available: bool = None,
        memory: int = None,
    ):
        self.accelerator_type = accelerator_type
        self.cpu = cpu
        self.gpu = gpu
        self.gpu_type = gpu_type
        self.instance_type = instance_type
        self.is_available = is_available
        self.memory = memory

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.accelerator_type is not None:
            result['AcceleratorType'] = self.accelerator_type
        if self.cpu is not None:
            result['Cpu'] = self.cpu
        if self.gpu is not None:
            result['Gpu'] = self.gpu
        if self.gpu_type is not None:
            result['GpuType'] = self.gpu_type
        if self.instance_type is not None:
            result['InstanceType'] = self.instance_type
        if self.is_available is not None:
            result['IsAvailable'] = self.is_available
        if self.memory is not None:
            result['Memory'] = self.memory
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('AcceleratorType') is not None:
            self.accelerator_type = m.get('AcceleratorType')
        if m.get('Cpu') is not None:
            self.cpu = m.get('Cpu')
        if m.get('Gpu') is not None:
            self.gpu = m.get('Gpu')
        if m.get('GpuType') is not None:
            self.gpu_type = m.get('GpuType')
        if m.get('InstanceType') is not None:
            self.instance_type = m.get('InstanceType')
        if m.get('IsAvailable') is not None:
            self.is_available = m.get('IsAvailable')
        if m.get('Memory') is not None:
            self.memory = m.get('Memory')
        return self


class ExtraPodSpec(TeaModel):
    def __init__(
        self,
        init_containers: List[ContainerSpec] = None,
        pod_annotations: Dict[str, str] = None,
        pod_labels: Dict[str, str] = None,
        shared_volume_mount_paths: List[str] = None,
        side_car_containers: List[ContainerSpec] = None,
    ):
        self.init_containers = init_containers
        self.pod_annotations = pod_annotations
        self.pod_labels = pod_labels
        self.shared_volume_mount_paths = shared_volume_mount_paths
        self.side_car_containers = side_car_containers

    def validate(self):
        if self.init_containers:
            for k in self.init_containers:
                if k:
                    k.validate()
        if self.side_car_containers:
            for k in self.side_car_containers:
                if k:
                    k.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        result['InitContainers'] = []
        if self.init_containers is not None:
            for k in self.init_containers:
                result['InitContainers'].append(k.to_map() if k else None)
        if self.pod_annotations is not None:
            result['PodAnnotations'] = self.pod_annotations
        if self.pod_labels is not None:
            result['PodLabels'] = self.pod_labels
        if self.shared_volume_mount_paths is not None:
            result['SharedVolumeMountPaths'] = self.shared_volume_mount_paths
        result['SideCarContainers'] = []
        if self.side_car_containers is not None:
            for k in self.side_car_containers:
                result['SideCarContainers'].append(k.to_map() if k else None)
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        self.init_containers = []
        if m.get('InitContainers') is not None:
            for k in m.get('InitContainers'):
                temp_model = ContainerSpec()
                self.init_containers.append(temp_model.from_map(k))
        if m.get('PodAnnotations') is not None:
            self.pod_annotations = m.get('PodAnnotations')
        if m.get('PodLabels') is not None:
            self.pod_labels = m.get('PodLabels')
        if m.get('SharedVolumeMountPaths') is not None:
            self.shared_volume_mount_paths = m.get('SharedVolumeMountPaths')
        self.side_car_containers = []
        if m.get('SideCarContainers') is not None:
            for k in m.get('SideCarContainers'):
                temp_model = ContainerSpec()
                self.side_car_containers.append(temp_model.from_map(k))
        return self


class GPUDetail(TeaModel):
    def __init__(
        self,
        gpu: str = None,
        gputype: str = None,
        gputype_full_name: str = None,
    ):
        self.gpu = gpu
        self.gputype = gputype
        self.gputype_full_name = gputype_full_name

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.gpu is not None:
            result['GPU'] = self.gpu
        if self.gputype is not None:
            result['GPUType'] = self.gputype
        if self.gputype_full_name is not None:
            result['GPUTypeFullName'] = self.gputype_full_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('GPU') is not None:
            self.gpu = m.get('GPU')
        if m.get('GPUType') is not None:
            self.gputype = m.get('GPUType')
        if m.get('GPUTypeFullName') is not None:
            self.gputype_full_name = m.get('GPUTypeFullName')
        return self


class ImageItem(TeaModel):
    def __init__(
        self,
        accelerator_type: str = None,
        author_id: str = None,
        framework: str = None,
        image_provider_type: str = None,
        image_tag: str = None,
        image_url: str = None,
        image_url_vpc: str = None,
    ):
        self.accelerator_type = accelerator_type
        self.author_id = author_id
        self.framework = framework
        self.image_provider_type = image_provider_type
        self.image_tag = image_tag
        self.image_url = image_url
        self.image_url_vpc = image_url_vpc

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.accelerator_type is not None:
            result['AcceleratorType'] = self.accelerator_type
        if self.author_id is not None:
            result['AuthorId'] = self.author_id
        if self.framework is not None:
            result['Framework'] = self.framework
        if self.image_provider_type is not None:
            result['ImageProviderType'] = self.image_provider_type
        if self.image_tag is not None:
            result['ImageTag'] = self.image_tag
        if self.image_url is not None:
            result['ImageUrl'] = self.image_url
        if self.image_url_vpc is not None:
            result['ImageUrlVpc'] = self.image_url_vpc
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('AcceleratorType') is not None:
            self.accelerator_type = m.get('AcceleratorType')
        if m.get('AuthorId') is not None:
            self.author_id = m.get('AuthorId')
        if m.get('Framework') is not None:
            self.framework = m.get('Framework')
        if m.get('ImageProviderType') is not None:
            self.image_provider_type = m.get('ImageProviderType')
        if m.get('ImageTag') is not None:
            self.image_tag = m.get('ImageTag')
        if m.get('ImageUrl') is not None:
            self.image_url = m.get('ImageUrl')
        if m.get('ImageUrlVpc') is not None:
            self.image_url_vpc = m.get('ImageUrlVpc')
        return self


class JobDebuggerConfig(TeaModel):
    def __init__(
        self,
        debugger_config_content: str = None,
        debugger_config_id: str = None,
        gmt_create_time: str = None,
        job_id: str = None,
    ):
        self.debugger_config_content = debugger_config_content
        self.debugger_config_id = debugger_config_id
        self.gmt_create_time = gmt_create_time
        self.job_id = job_id

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.debugger_config_content is not None:
            result['DebuggerConfigContent'] = self.debugger_config_content
        if self.debugger_config_id is not None:
            result['DebuggerConfigId'] = self.debugger_config_id
        if self.gmt_create_time is not None:
            result['GmtCreateTime'] = self.gmt_create_time
        if self.job_id is not None:
            result['JobId'] = self.job_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('DebuggerConfigContent') is not None:
            self.debugger_config_content = m.get('DebuggerConfigContent')
        if m.get('DebuggerConfigId') is not None:
            self.debugger_config_id = m.get('DebuggerConfigId')
        if m.get('GmtCreateTime') is not None:
            self.gmt_create_time = m.get('GmtCreateTime')
        if m.get('JobId') is not None:
            self.job_id = m.get('JobId')
        return self


class JobElasticSpec(TeaModel):
    def __init__(
        self,
        aimaster_type: str = None,
        enable_elastic_training: bool = None,
        max_parallelism: int = None,
        min_parallelism: int = None,
    ):
        self.aimaster_type = aimaster_type
        self.enable_elastic_training = enable_elastic_training
        self.max_parallelism = max_parallelism
        self.min_parallelism = min_parallelism

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.aimaster_type is not None:
            result['AIMasterType'] = self.aimaster_type
        if self.enable_elastic_training is not None:
            result['EnableElasticTraining'] = self.enable_elastic_training
        if self.max_parallelism is not None:
            result['MaxParallelism'] = self.max_parallelism
        if self.min_parallelism is not None:
            result['MinParallelism'] = self.min_parallelism
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('AIMasterType') is not None:
            self.aimaster_type = m.get('AIMasterType')
        if m.get('EnableElasticTraining') is not None:
            self.enable_elastic_training = m.get('EnableElasticTraining')
        if m.get('MaxParallelism') is not None:
            self.max_parallelism = m.get('MaxParallelism')
        if m.get('MinParallelism') is not None:
            self.min_parallelism = m.get('MinParallelism')
        return self


class JobItemCodeSource(TeaModel):
    def __init__(
        self,
        branch: str = None,
        code_source_id: str = None,
        commit: str = None,
        mount_path: str = None,
    ):
        self.branch = branch
        self.code_source_id = code_source_id
        self.commit = commit
        self.mount_path = mount_path

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.branch is not None:
            result['Branch'] = self.branch
        if self.code_source_id is not None:
            result['CodeSourceId'] = self.code_source_id
        if self.commit is not None:
            result['Commit'] = self.commit
        if self.mount_path is not None:
            result['MountPath'] = self.mount_path
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('Branch') is not None:
            self.branch = m.get('Branch')
        if m.get('CodeSourceId') is not None:
            self.code_source_id = m.get('CodeSourceId')
        if m.get('Commit') is not None:
            self.commit = m.get('Commit')
        if m.get('MountPath') is not None:
            self.mount_path = m.get('MountPath')
        return self


class JobItemDataSources(TeaModel):
    def __init__(
        self,
        data_source_id: str = None,
        mount_path: str = None,
    ):
        self.data_source_id = data_source_id
        self.mount_path = mount_path

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.data_source_id is not None:
            result['DataSourceId'] = self.data_source_id
        if self.mount_path is not None:
            result['MountPath'] = self.mount_path
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('DataSourceId') is not None:
            self.data_source_id = m.get('DataSourceId')
        if m.get('MountPath') is not None:
            self.mount_path = m.get('MountPath')
        return self


class ResourceConfig(TeaModel):
    def __init__(
        self,
        cpu: str = None,
        gpu: str = None,
        gputype: str = None,
        memory: str = None,
        shared_memory: str = None,
    ):
        self.cpu = cpu
        self.gpu = gpu
        self.gputype = gputype
        self.memory = memory
        self.shared_memory = shared_memory

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.cpu is not None:
            result['CPU'] = self.cpu
        if self.gpu is not None:
            result['GPU'] = self.gpu
        if self.gputype is not None:
            result['GPUType'] = self.gputype
        if self.memory is not None:
            result['Memory'] = self.memory
        if self.shared_memory is not None:
            result['SharedMemory'] = self.shared_memory
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('CPU') is not None:
            self.cpu = m.get('CPU')
        if m.get('GPU') is not None:
            self.gpu = m.get('GPU')
        if m.get('GPUType') is not None:
            self.gputype = m.get('GPUType')
        if m.get('Memory') is not None:
            self.memory = m.get('Memory')
        if m.get('SharedMemory') is not None:
            self.shared_memory = m.get('SharedMemory')
        return self


class JobSpec(TeaModel):
    def __init__(
        self,
        ecs_spec: str = None,
        extra_pod_spec: ExtraPodSpec = None,
        image: str = None,
        pod_count: int = None,
        resource_config: ResourceConfig = None,
        type: str = None,
        use_spot_instance: bool = None,
    ):
        self.ecs_spec = ecs_spec
        self.extra_pod_spec = extra_pod_spec
        self.image = image
        self.pod_count = pod_count
        self.resource_config = resource_config
        self.type = type
        self.use_spot_instance = use_spot_instance

    def validate(self):
        if self.extra_pod_spec:
            self.extra_pod_spec.validate()
        if self.resource_config:
            self.resource_config.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.ecs_spec is not None:
            result['EcsSpec'] = self.ecs_spec
        if self.extra_pod_spec is not None:
            result['ExtraPodSpec'] = self.extra_pod_spec.to_map()
        if self.image is not None:
            result['Image'] = self.image
        if self.pod_count is not None:
            result['PodCount'] = self.pod_count
        if self.resource_config is not None:
            result['ResourceConfig'] = self.resource_config.to_map()
        if self.type is not None:
            result['Type'] = self.type
        if self.use_spot_instance is not None:
            result['UseSpotInstance'] = self.use_spot_instance
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('EcsSpec') is not None:
            self.ecs_spec = m.get('EcsSpec')
        if m.get('ExtraPodSpec') is not None:
            temp_model = ExtraPodSpec()
            self.extra_pod_spec = temp_model.from_map(m['ExtraPodSpec'])
        if m.get('Image') is not None:
            self.image = m.get('Image')
        if m.get('PodCount') is not None:
            self.pod_count = m.get('PodCount')
        if m.get('ResourceConfig') is not None:
            temp_model = ResourceConfig()
            self.resource_config = temp_model.from_map(m['ResourceConfig'])
        if m.get('Type') is not None:
            self.type = m.get('Type')
        if m.get('UseSpotInstance') is not None:
            self.use_spot_instance = m.get('UseSpotInstance')
        return self


class JobSettings(TeaModel):
    def __init__(
        self,
        business_user_id: str = None,
        caller: str = None,
        enable_error_monitoring_in_aimaster: bool = None,
        enable_rdma: bool = None,
        enable_tide_resource: bool = None,
        error_monitoring_args: str = None,
        pipeline_id: str = None,
        tags: Dict[str, str] = None,
    ):
        self.business_user_id = business_user_id
        self.caller = caller
        self.enable_error_monitoring_in_aimaster = enable_error_monitoring_in_aimaster
        self.enable_rdma = enable_rdma
        self.enable_tide_resource = enable_tide_resource
        self.error_monitoring_args = error_monitoring_args
        self.pipeline_id = pipeline_id
        self.tags = tags

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.business_user_id is not None:
            result['BusinessUserId'] = self.business_user_id
        if self.caller is not None:
            result['Caller'] = self.caller
        if self.enable_error_monitoring_in_aimaster is not None:
            result['EnableErrorMonitoringInAIMaster'] = self.enable_error_monitoring_in_aimaster
        if self.enable_rdma is not None:
            result['EnableRDMA'] = self.enable_rdma
        if self.enable_tide_resource is not None:
            result['EnableTideResource'] = self.enable_tide_resource
        if self.error_monitoring_args is not None:
            result['ErrorMonitoringArgs'] = self.error_monitoring_args
        if self.pipeline_id is not None:
            result['PipelineId'] = self.pipeline_id
        if self.tags is not None:
            result['Tags'] = self.tags
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('BusinessUserId') is not None:
            self.business_user_id = m.get('BusinessUserId')
        if m.get('Caller') is not None:
            self.caller = m.get('Caller')
        if m.get('EnableErrorMonitoringInAIMaster') is not None:
            self.enable_error_monitoring_in_aimaster = m.get('EnableErrorMonitoringInAIMaster')
        if m.get('EnableRDMA') is not None:
            self.enable_rdma = m.get('EnableRDMA')
        if m.get('EnableTideResource') is not None:
            self.enable_tide_resource = m.get('EnableTideResource')
        if m.get('ErrorMonitoringArgs') is not None:
            self.error_monitoring_args = m.get('ErrorMonitoringArgs')
        if m.get('PipelineId') is not None:
            self.pipeline_id = m.get('PipelineId')
        if m.get('Tags') is not None:
            self.tags = m.get('Tags')
        return self


class JobItem(TeaModel):
    def __init__(
        self,
        code_source: JobItemCodeSource = None,
        data_sources: List[JobItemDataSources] = None,
        display_name: str = None,
        duration: int = None,
        enabled_debugger: bool = None,
        envs: Dict[str, str] = None,
        gmt_create_time: str = None,
        gmt_failed_time: str = None,
        gmt_finish_time: str = None,
        gmt_running_time: str = None,
        gmt_stopped_time: str = None,
        gmt_submitted_time: str = None,
        gmt_successed_time: str = None,
        job_id: str = None,
        job_specs: List[JobSpec] = None,
        job_type: str = None,
        priority: int = None,
        reason_code: str = None,
        reason_message: str = None,
        resource_id: str = None,
        resource_level: str = None,
        resource_name: str = None,
        settings: JobSettings = None,
        status: str = None,
        thirdparty_lib_dir: str = None,
        thirdparty_libs: List[str] = None,
        user_command: str = None,
        user_id: str = None,
        workspace_id: str = None,
        workspace_name: str = None,
    ):
        self.code_source = code_source
        self.data_sources = data_sources
        self.display_name = display_name
        self.duration = duration
        self.enabled_debugger = enabled_debugger
        self.envs = envs
        self.gmt_create_time = gmt_create_time
        self.gmt_failed_time = gmt_failed_time
        self.gmt_finish_time = gmt_finish_time
        self.gmt_running_time = gmt_running_time
        self.gmt_stopped_time = gmt_stopped_time
        self.gmt_submitted_time = gmt_submitted_time
        self.gmt_successed_time = gmt_successed_time
        self.job_id = job_id
        self.job_specs = job_specs
        self.job_type = job_type
        self.priority = priority
        self.reason_code = reason_code
        self.reason_message = reason_message
        self.resource_id = resource_id
        self.resource_level = resource_level
        self.resource_name = resource_name
        self.settings = settings
        self.status = status
        self.thirdparty_lib_dir = thirdparty_lib_dir
        self.thirdparty_libs = thirdparty_libs
        self.user_command = user_command
        self.user_id = user_id
        self.workspace_id = workspace_id
        self.workspace_name = workspace_name

    def validate(self):
        if self.code_source:
            self.code_source.validate()
        if self.data_sources:
            for k in self.data_sources:
                if k:
                    k.validate()
        if self.job_specs:
            for k in self.job_specs:
                if k:
                    k.validate()
        if self.settings:
            self.settings.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.code_source is not None:
            result['CodeSource'] = self.code_source.to_map()
        result['DataSources'] = []
        if self.data_sources is not None:
            for k in self.data_sources:
                result['DataSources'].append(k.to_map() if k else None)
        if self.display_name is not None:
            result['DisplayName'] = self.display_name
        if self.duration is not None:
            result['Duration'] = self.duration
        if self.enabled_debugger is not None:
            result['EnabledDebugger'] = self.enabled_debugger
        if self.envs is not None:
            result['Envs'] = self.envs
        if self.gmt_create_time is not None:
            result['GmtCreateTime'] = self.gmt_create_time
        if self.gmt_failed_time is not None:
            result['GmtFailedTime'] = self.gmt_failed_time
        if self.gmt_finish_time is not None:
            result['GmtFinishTime'] = self.gmt_finish_time
        if self.gmt_running_time is not None:
            result['GmtRunningTime'] = self.gmt_running_time
        if self.gmt_stopped_time is not None:
            result['GmtStoppedTime'] = self.gmt_stopped_time
        if self.gmt_submitted_time is not None:
            result['GmtSubmittedTime'] = self.gmt_submitted_time
        if self.gmt_successed_time is not None:
            result['GmtSuccessedTime'] = self.gmt_successed_time
        if self.job_id is not None:
            result['JobId'] = self.job_id
        result['JobSpecs'] = []
        if self.job_specs is not None:
            for k in self.job_specs:
                result['JobSpecs'].append(k.to_map() if k else None)
        if self.job_type is not None:
            result['JobType'] = self.job_type
        if self.priority is not None:
            result['Priority'] = self.priority
        if self.reason_code is not None:
            result['ReasonCode'] = self.reason_code
        if self.reason_message is not None:
            result['ReasonMessage'] = self.reason_message
        if self.resource_id is not None:
            result['ResourceId'] = self.resource_id
        if self.resource_level is not None:
            result['ResourceLevel'] = self.resource_level
        if self.resource_name is not None:
            result['ResourceName'] = self.resource_name
        if self.settings is not None:
            result['Settings'] = self.settings.to_map()
        if self.status is not None:
            result['Status'] = self.status
        if self.thirdparty_lib_dir is not None:
            result['ThirdpartyLibDir'] = self.thirdparty_lib_dir
        if self.thirdparty_libs is not None:
            result['ThirdpartyLibs'] = self.thirdparty_libs
        if self.user_command is not None:
            result['UserCommand'] = self.user_command
        if self.user_id is not None:
            result['UserId'] = self.user_id
        if self.workspace_id is not None:
            result['WorkspaceId'] = self.workspace_id
        if self.workspace_name is not None:
            result['WorkspaceName'] = self.workspace_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('CodeSource') is not None:
            temp_model = JobItemCodeSource()
            self.code_source = temp_model.from_map(m['CodeSource'])
        self.data_sources = []
        if m.get('DataSources') is not None:
            for k in m.get('DataSources'):
                temp_model = JobItemDataSources()
                self.data_sources.append(temp_model.from_map(k))
        if m.get('DisplayName') is not None:
            self.display_name = m.get('DisplayName')
        if m.get('Duration') is not None:
            self.duration = m.get('Duration')
        if m.get('EnabledDebugger') is not None:
            self.enabled_debugger = m.get('EnabledDebugger')
        if m.get('Envs') is not None:
            self.envs = m.get('Envs')
        if m.get('GmtCreateTime') is not None:
            self.gmt_create_time = m.get('GmtCreateTime')
        if m.get('GmtFailedTime') is not None:
            self.gmt_failed_time = m.get('GmtFailedTime')
        if m.get('GmtFinishTime') is not None:
            self.gmt_finish_time = m.get('GmtFinishTime')
        if m.get('GmtRunningTime') is not None:
            self.gmt_running_time = m.get('GmtRunningTime')
        if m.get('GmtStoppedTime') is not None:
            self.gmt_stopped_time = m.get('GmtStoppedTime')
        if m.get('GmtSubmittedTime') is not None:
            self.gmt_submitted_time = m.get('GmtSubmittedTime')
        if m.get('GmtSuccessedTime') is not None:
            self.gmt_successed_time = m.get('GmtSuccessedTime')
        if m.get('JobId') is not None:
            self.job_id = m.get('JobId')
        self.job_specs = []
        if m.get('JobSpecs') is not None:
            for k in m.get('JobSpecs'):
                temp_model = JobSpec()
                self.job_specs.append(temp_model.from_map(k))
        if m.get('JobType') is not None:
            self.job_type = m.get('JobType')
        if m.get('Priority') is not None:
            self.priority = m.get('Priority')
        if m.get('ReasonCode') is not None:
            self.reason_code = m.get('ReasonCode')
        if m.get('ReasonMessage') is not None:
            self.reason_message = m.get('ReasonMessage')
        if m.get('ResourceId') is not None:
            self.resource_id = m.get('ResourceId')
        if m.get('ResourceLevel') is not None:
            self.resource_level = m.get('ResourceLevel')
        if m.get('ResourceName') is not None:
            self.resource_name = m.get('ResourceName')
        if m.get('Settings') is not None:
            temp_model = JobSettings()
            self.settings = temp_model.from_map(m['Settings'])
        if m.get('Status') is not None:
            self.status = m.get('Status')
        if m.get('ThirdpartyLibDir') is not None:
            self.thirdparty_lib_dir = m.get('ThirdpartyLibDir')
        if m.get('ThirdpartyLibs') is not None:
            self.thirdparty_libs = m.get('ThirdpartyLibs')
        if m.get('UserCommand') is not None:
            self.user_command = m.get('UserCommand')
        if m.get('UserId') is not None:
            self.user_id = m.get('UserId')
        if m.get('WorkspaceId') is not None:
            self.workspace_id = m.get('WorkspaceId')
        if m.get('WorkspaceName') is not None:
            self.workspace_name = m.get('WorkspaceName')
        return self


class Member(TeaModel):
    def __init__(
        self,
        member_id: str = None,
        member_type: str = None,
    ):
        self.member_id = member_id
        self.member_type = member_type

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.member_id is not None:
            result['MemberId'] = self.member_id
        if self.member_type is not None:
            result['MemberType'] = self.member_type
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('MemberId') is not None:
            self.member_id = m.get('MemberId')
        if m.get('MemberType') is not None:
            self.member_type = m.get('MemberType')
        return self


class Metric(TeaModel):
    def __init__(
        self,
        time: int = None,
        value: float = None,
    ):
        self.time = time
        self.value = value

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.time is not None:
            result['Time'] = self.time
        if self.value is not None:
            result['Value'] = self.value
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('Time') is not None:
            self.time = m.get('Time')
        if m.get('Value') is not None:
            self.value = m.get('Value')
        return self


class NodeMetric(TeaModel):
    def __init__(
        self,
        metrics: List[Metric] = None,
        node_name: str = None,
    ):
        self.metrics = metrics
        self.node_name = node_name

    def validate(self):
        if self.metrics:
            for k in self.metrics:
                if k:
                    k.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        result['Metrics'] = []
        if self.metrics is not None:
            for k in self.metrics:
                result['Metrics'].append(k.to_map() if k else None)
        if self.node_name is not None:
            result['NodeName'] = self.node_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        self.metrics = []
        if m.get('Metrics') is not None:
            for k in m.get('Metrics'):
                temp_model = Metric()
                self.metrics.append(temp_model.from_map(k))
        if m.get('NodeName') is not None:
            self.node_name = m.get('NodeName')
        return self


class PodMetric(TeaModel):
    def __init__(
        self,
        metrics: List[Metric] = None,
        pod_id: str = None,
    ):
        self.metrics = metrics
        self.pod_id = pod_id

    def validate(self):
        if self.metrics:
            for k in self.metrics:
                if k:
                    k.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        result['Metrics'] = []
        if self.metrics is not None:
            for k in self.metrics:
                result['Metrics'].append(k.to_map() if k else None)
        if self.pod_id is not None:
            result['PodId'] = self.pod_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        self.metrics = []
        if m.get('Metrics') is not None:
            for k in m.get('Metrics'):
                temp_model = Metric()
                self.metrics.append(temp_model.from_map(k))
        if m.get('PodId') is not None:
            self.pod_id = m.get('PodId')
        return self


class QuotaDetail(TeaModel):
    def __init__(
        self,
        cpu: str = None,
        gpu: str = None,
        gpudetails: List[GPUDetail] = None,
        gputype: str = None,
        gputype_full_name: str = None,
        memory: str = None,
    ):
        self.cpu = cpu
        self.gpu = gpu
        self.gpudetails = gpudetails
        self.gputype = gputype
        self.gputype_full_name = gputype_full_name
        self.memory = memory

    def validate(self):
        if self.gpudetails:
            for k in self.gpudetails:
                if k:
                    k.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.cpu is not None:
            result['CPU'] = self.cpu
        if self.gpu is not None:
            result['GPU'] = self.gpu
        result['GPUDetails'] = []
        if self.gpudetails is not None:
            for k in self.gpudetails:
                result['GPUDetails'].append(k.to_map() if k else None)
        if self.gputype is not None:
            result['GPUType'] = self.gputype
        if self.gputype_full_name is not None:
            result['GPUTypeFullName'] = self.gputype_full_name
        if self.memory is not None:
            result['Memory'] = self.memory
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('CPU') is not None:
            self.cpu = m.get('CPU')
        if m.get('GPU') is not None:
            self.gpu = m.get('GPU')
        self.gpudetails = []
        if m.get('GPUDetails') is not None:
            for k in m.get('GPUDetails'):
                temp_model = GPUDetail()
                self.gpudetails.append(temp_model.from_map(k))
        if m.get('GPUType') is not None:
            self.gputype = m.get('GPUType')
        if m.get('GPUTypeFullName') is not None:
            self.gputype_full_name = m.get('GPUTypeFullName')
        if m.get('Memory') is not None:
            self.memory = m.get('Memory')
        return self


class Quota(TeaModel):
    def __init__(
        self,
        cluster_id: str = None,
        cluster_name: str = None,
        enable_tide_resource: bool = None,
        is_exclusive_quota: bool = None,
        quota_id: str = None,
        quota_name: str = None,
        quota_type: str = None,
        resource_level: str = None,
        total_quota: QuotaDetail = None,
        total_tide_quota: QuotaDetail = None,
        used_quota: QuotaDetail = None,
        used_tide_quota: QuotaDetail = None,
    ):
        self.cluster_id = cluster_id
        self.cluster_name = cluster_name
        self.enable_tide_resource = enable_tide_resource
        self.is_exclusive_quota = is_exclusive_quota
        self.quota_id = quota_id
        self.quota_name = quota_name
        self.quota_type = quota_type
        self.resource_level = resource_level
        self.total_quota = total_quota
        self.total_tide_quota = total_tide_quota
        self.used_quota = used_quota
        self.used_tide_quota = used_tide_quota

    def validate(self):
        if self.total_quota:
            self.total_quota.validate()
        if self.total_tide_quota:
            self.total_tide_quota.validate()
        if self.used_quota:
            self.used_quota.validate()
        if self.used_tide_quota:
            self.used_tide_quota.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.cluster_id is not None:
            result['ClusterId'] = self.cluster_id
        if self.cluster_name is not None:
            result['ClusterName'] = self.cluster_name
        if self.enable_tide_resource is not None:
            result['EnableTideResource'] = self.enable_tide_resource
        if self.is_exclusive_quota is not None:
            result['IsExclusiveQuota'] = self.is_exclusive_quota
        if self.quota_id is not None:
            result['QuotaId'] = self.quota_id
        if self.quota_name is not None:
            result['QuotaName'] = self.quota_name
        if self.quota_type is not None:
            result['QuotaType'] = self.quota_type
        if self.resource_level is not None:
            result['ResourceLevel'] = self.resource_level
        if self.total_quota is not None:
            result['TotalQuota'] = self.total_quota.to_map()
        if self.total_tide_quota is not None:
            result['TotalTideQuota'] = self.total_tide_quota.to_map()
        if self.used_quota is not None:
            result['UsedQuota'] = self.used_quota.to_map()
        if self.used_tide_quota is not None:
            result['UsedTideQuota'] = self.used_tide_quota.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('ClusterId') is not None:
            self.cluster_id = m.get('ClusterId')
        if m.get('ClusterName') is not None:
            self.cluster_name = m.get('ClusterName')
        if m.get('EnableTideResource') is not None:
            self.enable_tide_resource = m.get('EnableTideResource')
        if m.get('IsExclusiveQuota') is not None:
            self.is_exclusive_quota = m.get('IsExclusiveQuota')
        if m.get('QuotaId') is not None:
            self.quota_id = m.get('QuotaId')
        if m.get('QuotaName') is not None:
            self.quota_name = m.get('QuotaName')
        if m.get('QuotaType') is not None:
            self.quota_type = m.get('QuotaType')
        if m.get('ResourceLevel') is not None:
            self.resource_level = m.get('ResourceLevel')
        if m.get('TotalQuota') is not None:
            temp_model = QuotaDetail()
            self.total_quota = temp_model.from_map(m['TotalQuota'])
        if m.get('TotalTideQuota') is not None:
            temp_model = QuotaDetail()
            self.total_tide_quota = temp_model.from_map(m['TotalTideQuota'])
        if m.get('UsedQuota') is not None:
            temp_model = QuotaDetail()
            self.used_quota = temp_model.from_map(m['UsedQuota'])
        if m.get('UsedTideQuota') is not None:
            temp_model = QuotaDetail()
            self.used_tide_quota = temp_model.from_map(m['UsedTideQuota'])
        return self


class Resources(TeaModel):
    def __init__(
        self,
        cpu: str = None,
        gpu: str = None,
        memory: str = None,
    ):
        self.cpu = cpu
        self.gpu = gpu
        self.memory = memory

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.cpu is not None:
            result['CPU'] = self.cpu
        if self.gpu is not None:
            result['GPU'] = self.gpu
        if self.memory is not None:
            result['Memory'] = self.memory
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('CPU') is not None:
            self.cpu = m.get('CPU')
        if m.get('GPU') is not None:
            self.gpu = m.get('GPU')
        if m.get('Memory') is not None:
            self.memory = m.get('Memory')
        return self


class SmartCache(TeaModel):
    def __init__(
        self,
        cache_worker_num: int = None,
        cache_worker_size: int = None,
        description: str = None,
        display_name: str = None,
        duration: str = None,
        endpoint: str = None,
        file_system_id: str = None,
        gmt_create_time: str = None,
        gmt_modify_time: str = None,
        mount_path: str = None,
        options: str = None,
        path: str = None,
        smart_cache_id: str = None,
        status: str = None,
        type: str = None,
        user_id: str = None,
    ):
        self.cache_worker_num = cache_worker_num
        self.cache_worker_size = cache_worker_size
        self.description = description
        self.display_name = display_name
        self.duration = duration
        self.endpoint = endpoint
        self.file_system_id = file_system_id
        self.gmt_create_time = gmt_create_time
        self.gmt_modify_time = gmt_modify_time
        self.mount_path = mount_path
        self.options = options
        self.path = path
        self.smart_cache_id = smart_cache_id
        self.status = status
        self.type = type
        self.user_id = user_id

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.cache_worker_num is not None:
            result['CacheWorkerNum'] = self.cache_worker_num
        if self.cache_worker_size is not None:
            result['CacheWorkerSize'] = self.cache_worker_size
        if self.description is not None:
            result['Description'] = self.description
        if self.display_name is not None:
            result['DisplayName'] = self.display_name
        if self.duration is not None:
            result['Duration'] = self.duration
        if self.endpoint is not None:
            result['Endpoint'] = self.endpoint
        if self.file_system_id is not None:
            result['FileSystemId'] = self.file_system_id
        if self.gmt_create_time is not None:
            result['GmtCreateTime'] = self.gmt_create_time
        if self.gmt_modify_time is not None:
            result['GmtModifyTime'] = self.gmt_modify_time
        if self.mount_path is not None:
            result['MountPath'] = self.mount_path
        if self.options is not None:
            result['Options'] = self.options
        if self.path is not None:
            result['Path'] = self.path
        if self.smart_cache_id is not None:
            result['SmartCacheId'] = self.smart_cache_id
        if self.status is not None:
            result['Status'] = self.status
        if self.type is not None:
            result['Type'] = self.type
        if self.user_id is not None:
            result['UserId'] = self.user_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('CacheWorkerNum') is not None:
            self.cache_worker_num = m.get('CacheWorkerNum')
        if m.get('CacheWorkerSize') is not None:
            self.cache_worker_size = m.get('CacheWorkerSize')
        if m.get('Description') is not None:
            self.description = m.get('Description')
        if m.get('DisplayName') is not None:
            self.display_name = m.get('DisplayName')
        if m.get('Duration') is not None:
            self.duration = m.get('Duration')
        if m.get('Endpoint') is not None:
            self.endpoint = m.get('Endpoint')
        if m.get('FileSystemId') is not None:
            self.file_system_id = m.get('FileSystemId')
        if m.get('GmtCreateTime') is not None:
            self.gmt_create_time = m.get('GmtCreateTime')
        if m.get('GmtModifyTime') is not None:
            self.gmt_modify_time = m.get('GmtModifyTime')
        if m.get('MountPath') is not None:
            self.mount_path = m.get('MountPath')
        if m.get('Options') is not None:
            self.options = m.get('Options')
        if m.get('Path') is not None:
            self.path = m.get('Path')
        if m.get('SmartCacheId') is not None:
            self.smart_cache_id = m.get('SmartCacheId')
        if m.get('Status') is not None:
            self.status = m.get('Status')
        if m.get('Type') is not None:
            self.type = m.get('Type')
        if m.get('UserId') is not None:
            self.user_id = m.get('UserId')
        return self


class Tensorboard(TeaModel):
    def __init__(
        self,
        data_source_id: str = None,
        display_name: str = None,
        duration: str = None,
        gmt_create_time: str = None,
        gmt_modify_time: str = None,
        job_id: str = None,
        reason_code: str = None,
        reason_message: str = None,
        request_id: str = None,
        status: str = None,
        summary_path: str = None,
        tensorboard_id: str = None,
        tensorboard_url: str = None,
        user_id: str = None,
    ):
        self.data_source_id = data_source_id
        self.display_name = display_name
        self.duration = duration
        self.gmt_create_time = gmt_create_time
        self.gmt_modify_time = gmt_modify_time
        self.job_id = job_id
        self.reason_code = reason_code
        self.reason_message = reason_message
        self.request_id = request_id
        self.status = status
        self.summary_path = summary_path
        self.tensorboard_id = tensorboard_id
        self.tensorboard_url = tensorboard_url
        self.user_id = user_id

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.data_source_id is not None:
            result['DataSourceId'] = self.data_source_id
        if self.display_name is not None:
            result['DisplayName'] = self.display_name
        if self.duration is not None:
            result['Duration'] = self.duration
        if self.gmt_create_time is not None:
            result['GmtCreateTime'] = self.gmt_create_time
        if self.gmt_modify_time is not None:
            result['GmtModifyTime'] = self.gmt_modify_time
        if self.job_id is not None:
            result['JobId'] = self.job_id
        if self.reason_code is not None:
            result['ReasonCode'] = self.reason_code
        if self.reason_message is not None:
            result['ReasonMessage'] = self.reason_message
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        if self.status is not None:
            result['Status'] = self.status
        if self.summary_path is not None:
            result['SummaryPath'] = self.summary_path
        if self.tensorboard_id is not None:
            result['TensorboardId'] = self.tensorboard_id
        if self.tensorboard_url is not None:
            result['TensorboardUrl'] = self.tensorboard_url
        if self.user_id is not None:
            result['UserId'] = self.user_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('DataSourceId') is not None:
            self.data_source_id = m.get('DataSourceId')
        if m.get('DisplayName') is not None:
            self.display_name = m.get('DisplayName')
        if m.get('Duration') is not None:
            self.duration = m.get('Duration')
        if m.get('GmtCreateTime') is not None:
            self.gmt_create_time = m.get('GmtCreateTime')
        if m.get('GmtModifyTime') is not None:
            self.gmt_modify_time = m.get('GmtModifyTime')
        if m.get('JobId') is not None:
            self.job_id = m.get('JobId')
        if m.get('ReasonCode') is not None:
            self.reason_code = m.get('ReasonCode')
        if m.get('ReasonMessage') is not None:
            self.reason_message = m.get('ReasonMessage')
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        if m.get('Status') is not None:
            self.status = m.get('Status')
        if m.get('SummaryPath') is not None:
            self.summary_path = m.get('SummaryPath')
        if m.get('TensorboardId') is not None:
            self.tensorboard_id = m.get('TensorboardId')
        if m.get('TensorboardUrl') is not None:
            self.tensorboard_url = m.get('TensorboardUrl')
        if m.get('UserId') is not None:
            self.user_id = m.get('UserId')
        return self


class Workspace(TeaModel):
    def __init__(
        self,
        creator: str = None,
        gmt_create_time: str = None,
        gmt_modify_time: str = None,
        members: List[Member] = None,
        quotas: List[Quota] = None,
        total_resources: Resources = None,
        workspace_admins: List[Member] = None,
        workspace_id: str = None,
        workspace_name: str = None,
    ):
        self.creator = creator
        self.gmt_create_time = gmt_create_time
        self.gmt_modify_time = gmt_modify_time
        self.members = members
        self.quotas = quotas
        self.total_resources = total_resources
        self.workspace_admins = workspace_admins
        self.workspace_id = workspace_id
        self.workspace_name = workspace_name

    def validate(self):
        if self.members:
            for k in self.members:
                if k:
                    k.validate()
        if self.quotas:
            for k in self.quotas:
                if k:
                    k.validate()
        if self.total_resources:
            self.total_resources.validate()
        if self.workspace_admins:
            for k in self.workspace_admins:
                if k:
                    k.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.creator is not None:
            result['Creator'] = self.creator
        if self.gmt_create_time is not None:
            result['GmtCreateTime'] = self.gmt_create_time
        if self.gmt_modify_time is not None:
            result['GmtModifyTime'] = self.gmt_modify_time
        result['Members'] = []
        if self.members is not None:
            for k in self.members:
                result['Members'].append(k.to_map() if k else None)
        result['Quotas'] = []
        if self.quotas is not None:
            for k in self.quotas:
                result['Quotas'].append(k.to_map() if k else None)
        if self.total_resources is not None:
            result['TotalResources'] = self.total_resources.to_map()
        result['WorkspaceAdmins'] = []
        if self.workspace_admins is not None:
            for k in self.workspace_admins:
                result['WorkspaceAdmins'].append(k.to_map() if k else None)
        if self.workspace_id is not None:
            result['WorkspaceId'] = self.workspace_id
        if self.workspace_name is not None:
            result['WorkspaceName'] = self.workspace_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('Creator') is not None:
            self.creator = m.get('Creator')
        if m.get('GmtCreateTime') is not None:
            self.gmt_create_time = m.get('GmtCreateTime')
        if m.get('GmtModifyTime') is not None:
            self.gmt_modify_time = m.get('GmtModifyTime')
        self.members = []
        if m.get('Members') is not None:
            for k in m.get('Members'):
                temp_model = Member()
                self.members.append(temp_model.from_map(k))
        self.quotas = []
        if m.get('Quotas') is not None:
            for k in m.get('Quotas'):
                temp_model = Quota()
                self.quotas.append(temp_model.from_map(k))
        if m.get('TotalResources') is not None:
            temp_model = Resources()
            self.total_resources = temp_model.from_map(m['TotalResources'])
        self.workspace_admins = []
        if m.get('WorkspaceAdmins') is not None:
            for k in m.get('WorkspaceAdmins'):
                temp_model = Member()
                self.workspace_admins.append(temp_model.from_map(k))
        if m.get('WorkspaceId') is not None:
            self.workspace_id = m.get('WorkspaceId')
        if m.get('WorkspaceName') is not None:
            self.workspace_name = m.get('WorkspaceName')
        return self


class CreateJobRequestCodeSource(TeaModel):
    def __init__(
        self,
        branch: str = None,
        code_source_id: str = None,
        commit: str = None,
        mount_path: str = None,
    ):
        self.branch = branch
        self.code_source_id = code_source_id
        self.commit = commit
        self.mount_path = mount_path

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.branch is not None:
            result['Branch'] = self.branch
        if self.code_source_id is not None:
            result['CodeSourceId'] = self.code_source_id
        if self.commit is not None:
            result['Commit'] = self.commit
        if self.mount_path is not None:
            result['MountPath'] = self.mount_path
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('Branch') is not None:
            self.branch = m.get('Branch')
        if m.get('CodeSourceId') is not None:
            self.code_source_id = m.get('CodeSourceId')
        if m.get('Commit') is not None:
            self.commit = m.get('Commit')
        if m.get('MountPath') is not None:
            self.mount_path = m.get('MountPath')
        return self


class CreateJobRequestDataSources(TeaModel):
    def __init__(
        self,
        data_source_id: str = None,
        mount_path: str = None,
    ):
        self.data_source_id = data_source_id
        self.mount_path = mount_path

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.data_source_id is not None:
            result['DataSourceId'] = self.data_source_id
        if self.mount_path is not None:
            result['MountPath'] = self.mount_path
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('DataSourceId') is not None:
            self.data_source_id = m.get('DataSourceId')
        if m.get('MountPath') is not None:
            self.mount_path = m.get('MountPath')
        return self


class CreateJobRequestUserVpc(TeaModel):
    def __init__(
        self,
        extended_cidrs: List[str] = None,
        security_group_id: str = None,
        switch_id: str = None,
        vpc_id: str = None,
    ):
        self.extended_cidrs = extended_cidrs
        self.security_group_id = security_group_id
        self.switch_id = switch_id
        self.vpc_id = vpc_id

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.extended_cidrs is not None:
            result['ExtendedCIDRs'] = self.extended_cidrs
        if self.security_group_id is not None:
            result['SecurityGroupId'] = self.security_group_id
        if self.switch_id is not None:
            result['SwitchId'] = self.switch_id
        if self.vpc_id is not None:
            result['VpcId'] = self.vpc_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('ExtendedCIDRs') is not None:
            self.extended_cidrs = m.get('ExtendedCIDRs')
        if m.get('SecurityGroupId') is not None:
            self.security_group_id = m.get('SecurityGroupId')
        if m.get('SwitchId') is not None:
            self.switch_id = m.get('SwitchId')
        if m.get('VpcId') is not None:
            self.vpc_id = m.get('VpcId')
        return self


class CreateJobRequest(TeaModel):
    def __init__(
        self,
        code_source: CreateJobRequestCodeSource = None,
        data_sources: List[CreateJobRequestDataSources] = None,
        debugger_config_content: str = None,
        display_name: str = None,
        elastic_spec: JobElasticSpec = None,
        envs: Dict[str, str] = None,
        job_max_running_time_minutes: int = None,
        job_specs: List[JobSpec] = None,
        job_type: str = None,
        options: str = None,
        priority: int = None,
        resource_id: str = None,
        settings: JobSettings = None,
        thirdparty_lib_dir: str = None,
        thirdparty_libs: List[str] = None,
        user_command: str = None,
        user_vpc: CreateJobRequestUserVpc = None,
        workspace_id: str = None,
    ):
        self.code_source = code_source
        self.data_sources = data_sources
        self.debugger_config_content = debugger_config_content
        self.display_name = display_name
        self.elastic_spec = elastic_spec
        self.envs = envs
        self.job_max_running_time_minutes = job_max_running_time_minutes
        self.job_specs = job_specs
        self.job_type = job_type
        self.options = options
        self.priority = priority
        self.resource_id = resource_id
        self.settings = settings
        self.thirdparty_lib_dir = thirdparty_lib_dir
        self.thirdparty_libs = thirdparty_libs
        self.user_command = user_command
        self.user_vpc = user_vpc
        self.workspace_id = workspace_id

    def validate(self):
        if self.code_source:
            self.code_source.validate()
        if self.data_sources:
            for k in self.data_sources:
                if k:
                    k.validate()
        if self.elastic_spec:
            self.elastic_spec.validate()
        if self.job_specs:
            for k in self.job_specs:
                if k:
                    k.validate()
        if self.settings:
            self.settings.validate()
        if self.user_vpc:
            self.user_vpc.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.code_source is not None:
            result['CodeSource'] = self.code_source.to_map()
        result['DataSources'] = []
        if self.data_sources is not None:
            for k in self.data_sources:
                result['DataSources'].append(k.to_map() if k else None)
        if self.debugger_config_content is not None:
            result['DebuggerConfigContent'] = self.debugger_config_content
        if self.display_name is not None:
            result['DisplayName'] = self.display_name
        if self.elastic_spec is not None:
            result['ElasticSpec'] = self.elastic_spec.to_map()
        if self.envs is not None:
            result['Envs'] = self.envs
        if self.job_max_running_time_minutes is not None:
            result['JobMaxRunningTimeMinutes'] = self.job_max_running_time_minutes
        result['JobSpecs'] = []
        if self.job_specs is not None:
            for k in self.job_specs:
                result['JobSpecs'].append(k.to_map() if k else None)
        if self.job_type is not None:
            result['JobType'] = self.job_type
        if self.options is not None:
            result['Options'] = self.options
        if self.priority is not None:
            result['Priority'] = self.priority
        if self.resource_id is not None:
            result['ResourceId'] = self.resource_id
        if self.settings is not None:
            result['Settings'] = self.settings.to_map()
        if self.thirdparty_lib_dir is not None:
            result['ThirdpartyLibDir'] = self.thirdparty_lib_dir
        if self.thirdparty_libs is not None:
            result['ThirdpartyLibs'] = self.thirdparty_libs
        if self.user_command is not None:
            result['UserCommand'] = self.user_command
        if self.user_vpc is not None:
            result['UserVpc'] = self.user_vpc.to_map()
        if self.workspace_id is not None:
            result['WorkspaceId'] = self.workspace_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('CodeSource') is not None:
            temp_model = CreateJobRequestCodeSource()
            self.code_source = temp_model.from_map(m['CodeSource'])
        self.data_sources = []
        if m.get('DataSources') is not None:
            for k in m.get('DataSources'):
                temp_model = CreateJobRequestDataSources()
                self.data_sources.append(temp_model.from_map(k))
        if m.get('DebuggerConfigContent') is not None:
            self.debugger_config_content = m.get('DebuggerConfigContent')
        if m.get('DisplayName') is not None:
            self.display_name = m.get('DisplayName')
        if m.get('ElasticSpec') is not None:
            temp_model = JobElasticSpec()
            self.elastic_spec = temp_model.from_map(m['ElasticSpec'])
        if m.get('Envs') is not None:
            self.envs = m.get('Envs')
        if m.get('JobMaxRunningTimeMinutes') is not None:
            self.job_max_running_time_minutes = m.get('JobMaxRunningTimeMinutes')
        self.job_specs = []
        if m.get('JobSpecs') is not None:
            for k in m.get('JobSpecs'):
                temp_model = JobSpec()
                self.job_specs.append(temp_model.from_map(k))
        if m.get('JobType') is not None:
            self.job_type = m.get('JobType')
        if m.get('Options') is not None:
            self.options = m.get('Options')
        if m.get('Priority') is not None:
            self.priority = m.get('Priority')
        if m.get('ResourceId') is not None:
            self.resource_id = m.get('ResourceId')
        if m.get('Settings') is not None:
            temp_model = JobSettings()
            self.settings = temp_model.from_map(m['Settings'])
        if m.get('ThirdpartyLibDir') is not None:
            self.thirdparty_lib_dir = m.get('ThirdpartyLibDir')
        if m.get('ThirdpartyLibs') is not None:
            self.thirdparty_libs = m.get('ThirdpartyLibs')
        if m.get('UserCommand') is not None:
            self.user_command = m.get('UserCommand')
        if m.get('UserVpc') is not None:
            temp_model = CreateJobRequestUserVpc()
            self.user_vpc = temp_model.from_map(m['UserVpc'])
        if m.get('WorkspaceId') is not None:
            self.workspace_id = m.get('WorkspaceId')
        return self


class CreateJobResponseBody(TeaModel):
    def __init__(
        self,
        job_id: str = None,
        request_id: str = None,
    ):
        self.job_id = job_id
        self.request_id = request_id

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.job_id is not None:
            result['JobId'] = self.job_id
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('JobId') is not None:
            self.job_id = m.get('JobId')
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        return self


class CreateJobResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: CreateJobResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        self.validate_required(self.headers, 'headers')
        self.validate_required(self.status_code, 'status_code')
        self.validate_required(self.body, 'body')
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = CreateJobResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class CreateTensorboardRequest(TeaModel):
    def __init__(
        self,
        data_source_id: str = None,
        data_source_type: str = None,
        data_sources: List[DataSourceItem] = None,
        display_name: str = None,
        job_id: str = None,
        max_running_time_minutes: int = None,
        options: str = None,
        source_id: str = None,
        source_type: str = None,
        summary_path: str = None,
        summary_relative_path: str = None,
        uri: str = None,
        workspace_id: str = None,
    ):
        self.data_source_id = data_source_id
        self.data_source_type = data_source_type
        self.data_sources = data_sources
        self.display_name = display_name
        self.job_id = job_id
        self.max_running_time_minutes = max_running_time_minutes
        self.options = options
        self.source_id = source_id
        self.source_type = source_type
        self.summary_path = summary_path
        self.summary_relative_path = summary_relative_path
        self.uri = uri
        self.workspace_id = workspace_id

    def validate(self):
        if self.data_sources:
            for k in self.data_sources:
                if k:
                    k.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.data_source_id is not None:
            result['DataSourceId'] = self.data_source_id
        if self.data_source_type is not None:
            result['DataSourceType'] = self.data_source_type
        result['DataSources'] = []
        if self.data_sources is not None:
            for k in self.data_sources:
                result['DataSources'].append(k.to_map() if k else None)
        if self.display_name is not None:
            result['DisplayName'] = self.display_name
        if self.job_id is not None:
            result['JobId'] = self.job_id
        if self.max_running_time_minutes is not None:
            result['MaxRunningTimeMinutes'] = self.max_running_time_minutes
        if self.options is not None:
            result['Options'] = self.options
        if self.source_id is not None:
            result['SourceId'] = self.source_id
        if self.source_type is not None:
            result['SourceType'] = self.source_type
        if self.summary_path is not None:
            result['SummaryPath'] = self.summary_path
        if self.summary_relative_path is not None:
            result['SummaryRelativePath'] = self.summary_relative_path
        if self.uri is not None:
            result['Uri'] = self.uri
        if self.workspace_id is not None:
            result['WorkspaceId'] = self.workspace_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('DataSourceId') is not None:
            self.data_source_id = m.get('DataSourceId')
        if m.get('DataSourceType') is not None:
            self.data_source_type = m.get('DataSourceType')
        self.data_sources = []
        if m.get('DataSources') is not None:
            for k in m.get('DataSources'):
                temp_model = DataSourceItem()
                self.data_sources.append(temp_model.from_map(k))
        if m.get('DisplayName') is not None:
            self.display_name = m.get('DisplayName')
        if m.get('JobId') is not None:
            self.job_id = m.get('JobId')
        if m.get('MaxRunningTimeMinutes') is not None:
            self.max_running_time_minutes = m.get('MaxRunningTimeMinutes')
        if m.get('Options') is not None:
            self.options = m.get('Options')
        if m.get('SourceId') is not None:
            self.source_id = m.get('SourceId')
        if m.get('SourceType') is not None:
            self.source_type = m.get('SourceType')
        if m.get('SummaryPath') is not None:
            self.summary_path = m.get('SummaryPath')
        if m.get('SummaryRelativePath') is not None:
            self.summary_relative_path = m.get('SummaryRelativePath')
        if m.get('Uri') is not None:
            self.uri = m.get('Uri')
        if m.get('WorkspaceId') is not None:
            self.workspace_id = m.get('WorkspaceId')
        return self


class CreateTensorboardResponseBody(TeaModel):
    def __init__(
        self,
        data_source_id: str = None,
        job_id: str = None,
        request_id: str = None,
        tensorboard_id: str = None,
    ):
        self.data_source_id = data_source_id
        self.job_id = job_id
        self.request_id = request_id
        self.tensorboard_id = tensorboard_id

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.data_source_id is not None:
            result['DataSourceId'] = self.data_source_id
        if self.job_id is not None:
            result['JobId'] = self.job_id
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        if self.tensorboard_id is not None:
            result['TensorboardId'] = self.tensorboard_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('DataSourceId') is not None:
            self.data_source_id = m.get('DataSourceId')
        if m.get('JobId') is not None:
            self.job_id = m.get('JobId')
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        if m.get('TensorboardId') is not None:
            self.tensorboard_id = m.get('TensorboardId')
        return self


class CreateTensorboardResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: CreateTensorboardResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        self.validate_required(self.headers, 'headers')
        self.validate_required(self.status_code, 'status_code')
        self.validate_required(self.body, 'body')
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = CreateTensorboardResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class DeleteJobResponseBody(TeaModel):
    def __init__(
        self,
        job_id: str = None,
        request_id: str = None,
    ):
        self.job_id = job_id
        self.request_id = request_id

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.job_id is not None:
            result['JobId'] = self.job_id
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('JobId') is not None:
            self.job_id = m.get('JobId')
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        return self


class DeleteJobResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: DeleteJobResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        self.validate_required(self.headers, 'headers')
        self.validate_required(self.status_code, 'status_code')
        self.validate_required(self.body, 'body')
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = DeleteJobResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class DeleteTensorboardRequest(TeaModel):
    def __init__(
        self,
        workspace_id: str = None,
    ):
        self.workspace_id = workspace_id

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.workspace_id is not None:
            result['WorkspaceId'] = self.workspace_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('WorkspaceId') is not None:
            self.workspace_id = m.get('WorkspaceId')
        return self


class DeleteTensorboardResponseBody(TeaModel):
    def __init__(
        self,
        request_id: str = None,
        tensorboard_id: str = None,
    ):
        self.request_id = request_id
        self.tensorboard_id = tensorboard_id

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        if self.tensorboard_id is not None:
            result['TensorboardId'] = self.tensorboard_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        if m.get('TensorboardId') is not None:
            self.tensorboard_id = m.get('TensorboardId')
        return self


class DeleteTensorboardResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: DeleteTensorboardResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        self.validate_required(self.headers, 'headers')
        self.validate_required(self.status_code, 'status_code')
        self.validate_required(self.body, 'body')
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = DeleteTensorboardResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class GetJobResponseBodyCodeSource(TeaModel):
    def __init__(
        self,
        branch: str = None,
        code_source_id: str = None,
        commit: str = None,
        mount_path: str = None,
    ):
        self.branch = branch
        self.code_source_id = code_source_id
        self.commit = commit
        self.mount_path = mount_path

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.branch is not None:
            result['Branch'] = self.branch
        if self.code_source_id is not None:
            result['CodeSourceId'] = self.code_source_id
        if self.commit is not None:
            result['Commit'] = self.commit
        if self.mount_path is not None:
            result['MountPath'] = self.mount_path
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('Branch') is not None:
            self.branch = m.get('Branch')
        if m.get('CodeSourceId') is not None:
            self.code_source_id = m.get('CodeSourceId')
        if m.get('Commit') is not None:
            self.commit = m.get('Commit')
        if m.get('MountPath') is not None:
            self.mount_path = m.get('MountPath')
        return self


class GetJobResponseBodyDataSources(TeaModel):
    def __init__(
        self,
        data_source_id: str = None,
        mount_path: str = None,
    ):
        self.data_source_id = data_source_id
        self.mount_path = mount_path

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.data_source_id is not None:
            result['DataSourceId'] = self.data_source_id
        if self.mount_path is not None:
            result['MountPath'] = self.mount_path
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('DataSourceId') is not None:
            self.data_source_id = m.get('DataSourceId')
        if m.get('MountPath') is not None:
            self.mount_path = m.get('MountPath')
        return self


class GetJobResponseBodyPodsHistoryPods(TeaModel):
    def __init__(
        self,
        gmt_create_time: str = None,
        gmt_finish_time: str = None,
        gmt_start_time: str = None,
        ip: str = None,
        pod_id: str = None,
        pod_uid: str = None,
        status: str = None,
        type: str = None,
    ):
        self.gmt_create_time = gmt_create_time
        self.gmt_finish_time = gmt_finish_time
        self.gmt_start_time = gmt_start_time
        self.ip = ip
        self.pod_id = pod_id
        self.pod_uid = pod_uid
        self.status = status
        self.type = type

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.gmt_create_time is not None:
            result['GmtCreateTime'] = self.gmt_create_time
        if self.gmt_finish_time is not None:
            result['GmtFinishTime'] = self.gmt_finish_time
        if self.gmt_start_time is not None:
            result['GmtStartTime'] = self.gmt_start_time
        if self.ip is not None:
            result['Ip'] = self.ip
        if self.pod_id is not None:
            result['PodId'] = self.pod_id
        if self.pod_uid is not None:
            result['PodUid'] = self.pod_uid
        if self.status is not None:
            result['Status'] = self.status
        if self.type is not None:
            result['Type'] = self.type
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('GmtCreateTime') is not None:
            self.gmt_create_time = m.get('GmtCreateTime')
        if m.get('GmtFinishTime') is not None:
            self.gmt_finish_time = m.get('GmtFinishTime')
        if m.get('GmtStartTime') is not None:
            self.gmt_start_time = m.get('GmtStartTime')
        if m.get('Ip') is not None:
            self.ip = m.get('Ip')
        if m.get('PodId') is not None:
            self.pod_id = m.get('PodId')
        if m.get('PodUid') is not None:
            self.pod_uid = m.get('PodUid')
        if m.get('Status') is not None:
            self.status = m.get('Status')
        if m.get('Type') is not None:
            self.type = m.get('Type')
        return self


class GetJobResponseBodyPods(TeaModel):
    def __init__(
        self,
        gmt_create_time: str = None,
        gmt_finish_time: str = None,
        gmt_start_time: str = None,
        history_pods: List[GetJobResponseBodyPodsHistoryPods] = None,
        ip: str = None,
        pod_id: str = None,
        pod_uid: str = None,
        status: str = None,
        type: str = None,
    ):
        self.gmt_create_time = gmt_create_time
        self.gmt_finish_time = gmt_finish_time
        self.gmt_start_time = gmt_start_time
        self.history_pods = history_pods
        self.ip = ip
        self.pod_id = pod_id
        self.pod_uid = pod_uid
        self.status = status
        self.type = type

    def validate(self):
        if self.history_pods:
            for k in self.history_pods:
                if k:
                    k.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.gmt_create_time is not None:
            result['GmtCreateTime'] = self.gmt_create_time
        if self.gmt_finish_time is not None:
            result['GmtFinishTime'] = self.gmt_finish_time
        if self.gmt_start_time is not None:
            result['GmtStartTime'] = self.gmt_start_time
        result['HistoryPods'] = []
        if self.history_pods is not None:
            for k in self.history_pods:
                result['HistoryPods'].append(k.to_map() if k else None)
        if self.ip is not None:
            result['Ip'] = self.ip
        if self.pod_id is not None:
            result['PodId'] = self.pod_id
        if self.pod_uid is not None:
            result['PodUid'] = self.pod_uid
        if self.status is not None:
            result['Status'] = self.status
        if self.type is not None:
            result['Type'] = self.type
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('GmtCreateTime') is not None:
            self.gmt_create_time = m.get('GmtCreateTime')
        if m.get('GmtFinishTime') is not None:
            self.gmt_finish_time = m.get('GmtFinishTime')
        if m.get('GmtStartTime') is not None:
            self.gmt_start_time = m.get('GmtStartTime')
        self.history_pods = []
        if m.get('HistoryPods') is not None:
            for k in m.get('HistoryPods'):
                temp_model = GetJobResponseBodyPodsHistoryPods()
                self.history_pods.append(temp_model.from_map(k))
        if m.get('Ip') is not None:
            self.ip = m.get('Ip')
        if m.get('PodId') is not None:
            self.pod_id = m.get('PodId')
        if m.get('PodUid') is not None:
            self.pod_uid = m.get('PodUid')
        if m.get('Status') is not None:
            self.status = m.get('Status')
        if m.get('Type') is not None:
            self.type = m.get('Type')
        return self


class GetJobResponseBody(TeaModel):
    def __init__(
        self,
        cluster_id: str = None,
        code_source: GetJobResponseBodyCodeSource = None,
        data_sources: List[GetJobResponseBodyDataSources] = None,
        display_name: str = None,
        duration: int = None,
        elastic_spec: JobElasticSpec = None,
        enabled_debugger: bool = None,
        envs: Dict[str, str] = None,
        gmt_create_time: str = None,
        gmt_failed_time: str = None,
        gmt_finish_time: str = None,
        gmt_running_time: str = None,
        gmt_stopped_time: str = None,
        gmt_submitted_time: str = None,
        gmt_successed_time: str = None,
        job_id: str = None,
        job_specs: List[JobSpec] = None,
        job_type: str = None,
        pods: List[GetJobResponseBodyPods] = None,
        priority: int = None,
        reason_code: str = None,
        reason_message: str = None,
        request_id: str = None,
        resource_id: str = None,
        resource_level: str = None,
        settings: JobSettings = None,
        status: str = None,
        thirdparty_lib_dir: str = None,
        thirdparty_libs: List[str] = None,
        user_command: str = None,
        user_id: str = None,
        workspace_id: str = None,
        workspace_name: str = None,
    ):
        self.cluster_id = cluster_id
        self.code_source = code_source
        self.data_sources = data_sources
        self.display_name = display_name
        self.duration = duration
        self.elastic_spec = elastic_spec
        self.enabled_debugger = enabled_debugger
        self.envs = envs
        self.gmt_create_time = gmt_create_time
        self.gmt_failed_time = gmt_failed_time
        self.gmt_finish_time = gmt_finish_time
        self.gmt_running_time = gmt_running_time
        self.gmt_stopped_time = gmt_stopped_time
        self.gmt_submitted_time = gmt_submitted_time
        self.gmt_successed_time = gmt_successed_time
        self.job_id = job_id
        self.job_specs = job_specs
        self.job_type = job_type
        self.pods = pods
        self.priority = priority
        self.reason_code = reason_code
        self.reason_message = reason_message
        self.request_id = request_id
        self.resource_id = resource_id
        self.resource_level = resource_level
        self.settings = settings
        self.status = status
        self.thirdparty_lib_dir = thirdparty_lib_dir
        self.thirdparty_libs = thirdparty_libs
        self.user_command = user_command
        self.user_id = user_id
        self.workspace_id = workspace_id
        self.workspace_name = workspace_name

    def validate(self):
        if self.code_source:
            self.code_source.validate()
        if self.data_sources:
            for k in self.data_sources:
                if k:
                    k.validate()
        if self.elastic_spec:
            self.elastic_spec.validate()
        if self.job_specs:
            for k in self.job_specs:
                if k:
                    k.validate()
        if self.pods:
            for k in self.pods:
                if k:
                    k.validate()
        if self.settings:
            self.settings.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.cluster_id is not None:
            result['ClusterId'] = self.cluster_id
        if self.code_source is not None:
            result['CodeSource'] = self.code_source.to_map()
        result['DataSources'] = []
        if self.data_sources is not None:
            for k in self.data_sources:
                result['DataSources'].append(k.to_map() if k else None)
        if self.display_name is not None:
            result['DisplayName'] = self.display_name
        if self.duration is not None:
            result['Duration'] = self.duration
        if self.elastic_spec is not None:
            result['ElasticSpec'] = self.elastic_spec.to_map()
        if self.enabled_debugger is not None:
            result['EnabledDebugger'] = self.enabled_debugger
        if self.envs is not None:
            result['Envs'] = self.envs
        if self.gmt_create_time is not None:
            result['GmtCreateTime'] = self.gmt_create_time
        if self.gmt_failed_time is not None:
            result['GmtFailedTime'] = self.gmt_failed_time
        if self.gmt_finish_time is not None:
            result['GmtFinishTime'] = self.gmt_finish_time
        if self.gmt_running_time is not None:
            result['GmtRunningTime'] = self.gmt_running_time
        if self.gmt_stopped_time is not None:
            result['GmtStoppedTime'] = self.gmt_stopped_time
        if self.gmt_submitted_time is not None:
            result['GmtSubmittedTime'] = self.gmt_submitted_time
        if self.gmt_successed_time is not None:
            result['GmtSuccessedTime'] = self.gmt_successed_time
        if self.job_id is not None:
            result['JobId'] = self.job_id
        result['JobSpecs'] = []
        if self.job_specs is not None:
            for k in self.job_specs:
                result['JobSpecs'].append(k.to_map() if k else None)
        if self.job_type is not None:
            result['JobType'] = self.job_type
        result['Pods'] = []
        if self.pods is not None:
            for k in self.pods:
                result['Pods'].append(k.to_map() if k else None)
        if self.priority is not None:
            result['Priority'] = self.priority
        if self.reason_code is not None:
            result['ReasonCode'] = self.reason_code
        if self.reason_message is not None:
            result['ReasonMessage'] = self.reason_message
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        if self.resource_id is not None:
            result['ResourceId'] = self.resource_id
        if self.resource_level is not None:
            result['ResourceLevel'] = self.resource_level
        if self.settings is not None:
            result['Settings'] = self.settings.to_map()
        if self.status is not None:
            result['Status'] = self.status
        if self.thirdparty_lib_dir is not None:
            result['ThirdpartyLibDir'] = self.thirdparty_lib_dir
        if self.thirdparty_libs is not None:
            result['ThirdpartyLibs'] = self.thirdparty_libs
        if self.user_command is not None:
            result['UserCommand'] = self.user_command
        if self.user_id is not None:
            result['UserId'] = self.user_id
        if self.workspace_id is not None:
            result['WorkspaceId'] = self.workspace_id
        if self.workspace_name is not None:
            result['WorkspaceName'] = self.workspace_name
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('ClusterId') is not None:
            self.cluster_id = m.get('ClusterId')
        if m.get('CodeSource') is not None:
            temp_model = GetJobResponseBodyCodeSource()
            self.code_source = temp_model.from_map(m['CodeSource'])
        self.data_sources = []
        if m.get('DataSources') is not None:
            for k in m.get('DataSources'):
                temp_model = GetJobResponseBodyDataSources()
                self.data_sources.append(temp_model.from_map(k))
        if m.get('DisplayName') is not None:
            self.display_name = m.get('DisplayName')
        if m.get('Duration') is not None:
            self.duration = m.get('Duration')
        if m.get('ElasticSpec') is not None:
            temp_model = JobElasticSpec()
            self.elastic_spec = temp_model.from_map(m['ElasticSpec'])
        if m.get('EnabledDebugger') is not None:
            self.enabled_debugger = m.get('EnabledDebugger')
        if m.get('Envs') is not None:
            self.envs = m.get('Envs')
        if m.get('GmtCreateTime') is not None:
            self.gmt_create_time = m.get('GmtCreateTime')
        if m.get('GmtFailedTime') is not None:
            self.gmt_failed_time = m.get('GmtFailedTime')
        if m.get('GmtFinishTime') is not None:
            self.gmt_finish_time = m.get('GmtFinishTime')
        if m.get('GmtRunningTime') is not None:
            self.gmt_running_time = m.get('GmtRunningTime')
        if m.get('GmtStoppedTime') is not None:
            self.gmt_stopped_time = m.get('GmtStoppedTime')
        if m.get('GmtSubmittedTime') is not None:
            self.gmt_submitted_time = m.get('GmtSubmittedTime')
        if m.get('GmtSuccessedTime') is not None:
            self.gmt_successed_time = m.get('GmtSuccessedTime')
        if m.get('JobId') is not None:
            self.job_id = m.get('JobId')
        self.job_specs = []
        if m.get('JobSpecs') is not None:
            for k in m.get('JobSpecs'):
                temp_model = JobSpec()
                self.job_specs.append(temp_model.from_map(k))
        if m.get('JobType') is not None:
            self.job_type = m.get('JobType')
        self.pods = []
        if m.get('Pods') is not None:
            for k in m.get('Pods'):
                temp_model = GetJobResponseBodyPods()
                self.pods.append(temp_model.from_map(k))
        if m.get('Priority') is not None:
            self.priority = m.get('Priority')
        if m.get('ReasonCode') is not None:
            self.reason_code = m.get('ReasonCode')
        if m.get('ReasonMessage') is not None:
            self.reason_message = m.get('ReasonMessage')
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        if m.get('ResourceId') is not None:
            self.resource_id = m.get('ResourceId')
        if m.get('ResourceLevel') is not None:
            self.resource_level = m.get('ResourceLevel')
        if m.get('Settings') is not None:
            temp_model = JobSettings()
            self.settings = temp_model.from_map(m['Settings'])
        if m.get('Status') is not None:
            self.status = m.get('Status')
        if m.get('ThirdpartyLibDir') is not None:
            self.thirdparty_lib_dir = m.get('ThirdpartyLibDir')
        if m.get('ThirdpartyLibs') is not None:
            self.thirdparty_libs = m.get('ThirdpartyLibs')
        if m.get('UserCommand') is not None:
            self.user_command = m.get('UserCommand')
        if m.get('UserId') is not None:
            self.user_id = m.get('UserId')
        if m.get('WorkspaceId') is not None:
            self.workspace_id = m.get('WorkspaceId')
        if m.get('WorkspaceName') is not None:
            self.workspace_name = m.get('WorkspaceName')
        return self


class GetJobResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: GetJobResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        self.validate_required(self.headers, 'headers')
        self.validate_required(self.status_code, 'status_code')
        self.validate_required(self.body, 'body')
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = GetJobResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class GetJobEventsRequest(TeaModel):
    def __init__(
        self,
        end_time: str = None,
        max_events_num: int = None,
        start_time: str = None,
    ):
        self.end_time = end_time
        self.max_events_num = max_events_num
        self.start_time = start_time

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.end_time is not None:
            result['EndTime'] = self.end_time
        if self.max_events_num is not None:
            result['MaxEventsNum'] = self.max_events_num
        if self.start_time is not None:
            result['StartTime'] = self.start_time
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('EndTime') is not None:
            self.end_time = m.get('EndTime')
        if m.get('MaxEventsNum') is not None:
            self.max_events_num = m.get('MaxEventsNum')
        if m.get('StartTime') is not None:
            self.start_time = m.get('StartTime')
        return self


class GetJobEventsResponseBody(TeaModel):
    def __init__(
        self,
        events: List[str] = None,
        job_id: str = None,
        request_id: int = None,
    ):
        self.events = events
        self.job_id = job_id
        self.request_id = request_id

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.events is not None:
            result['Events'] = self.events
        if self.job_id is not None:
            result['JobId'] = self.job_id
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('Events') is not None:
            self.events = m.get('Events')
        if m.get('JobId') is not None:
            self.job_id = m.get('JobId')
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        return self


class GetJobEventsResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: GetJobEventsResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        self.validate_required(self.headers, 'headers')
        self.validate_required(self.status_code, 'status_code')
        self.validate_required(self.body, 'body')
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = GetJobEventsResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class GetJobMetricsRequest(TeaModel):
    def __init__(
        self,
        end_time: str = None,
        metric_type: str = None,
        start_time: str = None,
        time_step: str = None,
        token: str = None,
    ):
        self.end_time = end_time
        self.metric_type = metric_type
        self.start_time = start_time
        self.time_step = time_step
        self.token = token

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.end_time is not None:
            result['EndTime'] = self.end_time
        if self.metric_type is not None:
            result['MetricType'] = self.metric_type
        if self.start_time is not None:
            result['StartTime'] = self.start_time
        if self.time_step is not None:
            result['TimeStep'] = self.time_step
        if self.token is not None:
            result['Token'] = self.token
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('EndTime') is not None:
            self.end_time = m.get('EndTime')
        if m.get('MetricType') is not None:
            self.metric_type = m.get('MetricType')
        if m.get('StartTime') is not None:
            self.start_time = m.get('StartTime')
        if m.get('TimeStep') is not None:
            self.time_step = m.get('TimeStep')
        if m.get('Token') is not None:
            self.token = m.get('Token')
        return self


class GetJobMetricsResponseBody(TeaModel):
    def __init__(
        self,
        job_id: str = None,
        pod_metrics: List[PodMetric] = None,
        request_id: str = None,
    ):
        self.job_id = job_id
        self.pod_metrics = pod_metrics
        self.request_id = request_id

    def validate(self):
        if self.pod_metrics:
            for k in self.pod_metrics:
                if k:
                    k.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.job_id is not None:
            result['JobId'] = self.job_id
        result['PodMetrics'] = []
        if self.pod_metrics is not None:
            for k in self.pod_metrics:
                result['PodMetrics'].append(k.to_map() if k else None)
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('JobId') is not None:
            self.job_id = m.get('JobId')
        self.pod_metrics = []
        if m.get('PodMetrics') is not None:
            for k in m.get('PodMetrics'):
                temp_model = PodMetric()
                self.pod_metrics.append(temp_model.from_map(k))
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        return self


class GetJobMetricsResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: GetJobMetricsResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        self.validate_required(self.headers, 'headers')
        self.validate_required(self.status_code, 'status_code')
        self.validate_required(self.body, 'body')
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = GetJobMetricsResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class GetPodEventsRequest(TeaModel):
    def __init__(
        self,
        end_time: str = None,
        max_events_num: int = None,
        pod_uid: str = None,
        start_time: str = None,
    ):
        self.end_time = end_time
        self.max_events_num = max_events_num
        self.pod_uid = pod_uid
        self.start_time = start_time

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.end_time is not None:
            result['EndTime'] = self.end_time
        if self.max_events_num is not None:
            result['MaxEventsNum'] = self.max_events_num
        if self.pod_uid is not None:
            result['PodUid'] = self.pod_uid
        if self.start_time is not None:
            result['StartTime'] = self.start_time
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('EndTime') is not None:
            self.end_time = m.get('EndTime')
        if m.get('MaxEventsNum') is not None:
            self.max_events_num = m.get('MaxEventsNum')
        if m.get('PodUid') is not None:
            self.pod_uid = m.get('PodUid')
        if m.get('StartTime') is not None:
            self.start_time = m.get('StartTime')
        return self


class GetPodEventsResponseBody(TeaModel):
    def __init__(
        self,
        events: List[str] = None,
        job_id: str = None,
        pod_id: str = None,
        pod_uid: str = None,
        request_id: str = None,
    ):
        self.events = events
        self.job_id = job_id
        self.pod_id = pod_id
        self.pod_uid = pod_uid
        self.request_id = request_id

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.events is not None:
            result['Events'] = self.events
        if self.job_id is not None:
            result['JobId'] = self.job_id
        if self.pod_id is not None:
            result['PodId'] = self.pod_id
        if self.pod_uid is not None:
            result['PodUid'] = self.pod_uid
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('Events') is not None:
            self.events = m.get('Events')
        if m.get('JobId') is not None:
            self.job_id = m.get('JobId')
        if m.get('PodId') is not None:
            self.pod_id = m.get('PodId')
        if m.get('PodUid') is not None:
            self.pod_uid = m.get('PodUid')
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        return self


class GetPodEventsResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: GetPodEventsResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        self.validate_required(self.headers, 'headers')
        self.validate_required(self.status_code, 'status_code')
        self.validate_required(self.body, 'body')
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = GetPodEventsResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class GetPodLogsRequest(TeaModel):
    def __init__(
        self,
        download_to_file: bool = None,
        end_time: str = None,
        max_lines: int = None,
        pod_uid: str = None,
        start_time: str = None,
    ):
        self.download_to_file = download_to_file
        self.end_time = end_time
        self.max_lines = max_lines
        self.pod_uid = pod_uid
        self.start_time = start_time

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.download_to_file is not None:
            result['DownloadToFile'] = self.download_to_file
        if self.end_time is not None:
            result['EndTime'] = self.end_time
        if self.max_lines is not None:
            result['MaxLines'] = self.max_lines
        if self.pod_uid is not None:
            result['PodUid'] = self.pod_uid
        if self.start_time is not None:
            result['StartTime'] = self.start_time
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('DownloadToFile') is not None:
            self.download_to_file = m.get('DownloadToFile')
        if m.get('EndTime') is not None:
            self.end_time = m.get('EndTime')
        if m.get('MaxLines') is not None:
            self.max_lines = m.get('MaxLines')
        if m.get('PodUid') is not None:
            self.pod_uid = m.get('PodUid')
        if m.get('StartTime') is not None:
            self.start_time = m.get('StartTime')
        return self


class GetPodLogsResponseBody(TeaModel):
    def __init__(
        self,
        job_id: str = None,
        logs: List[str] = None,
        pod_id: str = None,
        pod_uid: str = None,
        request_id: str = None,
    ):
        self.job_id = job_id
        self.logs = logs
        self.pod_id = pod_id
        self.pod_uid = pod_uid
        self.request_id = request_id

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.job_id is not None:
            result['JobId'] = self.job_id
        if self.logs is not None:
            result['Logs'] = self.logs
        if self.pod_id is not None:
            result['PodId'] = self.pod_id
        if self.pod_uid is not None:
            result['PodUid'] = self.pod_uid
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('JobId') is not None:
            self.job_id = m.get('JobId')
        if m.get('Logs') is not None:
            self.logs = m.get('Logs')
        if m.get('PodId') is not None:
            self.pod_id = m.get('PodId')
        if m.get('PodUid') is not None:
            self.pod_uid = m.get('PodUid')
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        return self


class GetPodLogsResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: GetPodLogsResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        self.validate_required(self.headers, 'headers')
        self.validate_required(self.status_code, 'status_code')
        self.validate_required(self.body, 'body')
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = GetPodLogsResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class GetTensorboardRequest(TeaModel):
    def __init__(
        self,
        jod_id: str = None,
        workspace_id: str = None,
    ):
        self.jod_id = jod_id
        self.workspace_id = workspace_id

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.jod_id is not None:
            result['JodId'] = self.jod_id
        if self.workspace_id is not None:
            result['WorkspaceId'] = self.workspace_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('JodId') is not None:
            self.jod_id = m.get('JodId')
        if m.get('WorkspaceId') is not None:
            self.workspace_id = m.get('WorkspaceId')
        return self


class GetTensorboardResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: Tensorboard = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        self.validate_required(self.headers, 'headers')
        self.validate_required(self.status_code, 'status_code')
        self.validate_required(self.body, 'body')
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = Tensorboard()
            self.body = temp_model.from_map(m['body'])
        return self


class ListEcsSpecsRequest(TeaModel):
    def __init__(
        self,
        accelerator_type: str = None,
        order: str = None,
        page_number: int = None,
        page_size: int = None,
        sort_by: str = None,
    ):
        self.accelerator_type = accelerator_type
        self.order = order
        self.page_number = page_number
        self.page_size = page_size
        self.sort_by = sort_by

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.accelerator_type is not None:
            result['AcceleratorType'] = self.accelerator_type
        if self.order is not None:
            result['Order'] = self.order
        if self.page_number is not None:
            result['PageNumber'] = self.page_number
        if self.page_size is not None:
            result['PageSize'] = self.page_size
        if self.sort_by is not None:
            result['SortBy'] = self.sort_by
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('AcceleratorType') is not None:
            self.accelerator_type = m.get('AcceleratorType')
        if m.get('Order') is not None:
            self.order = m.get('Order')
        if m.get('PageNumber') is not None:
            self.page_number = m.get('PageNumber')
        if m.get('PageSize') is not None:
            self.page_size = m.get('PageSize')
        if m.get('SortBy') is not None:
            self.sort_by = m.get('SortBy')
        return self


class ListEcsSpecsResponseBody(TeaModel):
    def __init__(
        self,
        ecs_specs: List[EcsSpec] = None,
        request_id: str = None,
        total_count: int = None,
    ):
        self.ecs_specs = ecs_specs
        self.request_id = request_id
        self.total_count = total_count

    def validate(self):
        if self.ecs_specs:
            for k in self.ecs_specs:
                if k:
                    k.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        result['EcsSpecs'] = []
        if self.ecs_specs is not None:
            for k in self.ecs_specs:
                result['EcsSpecs'].append(k.to_map() if k else None)
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        if self.total_count is not None:
            result['TotalCount'] = self.total_count
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        self.ecs_specs = []
        if m.get('EcsSpecs') is not None:
            for k in m.get('EcsSpecs'):
                temp_model = EcsSpec()
                self.ecs_specs.append(temp_model.from_map(k))
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        if m.get('TotalCount') is not None:
            self.total_count = m.get('TotalCount')
        return self


class ListEcsSpecsResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: ListEcsSpecsResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        self.validate_required(self.headers, 'headers')
        self.validate_required(self.status_code, 'status_code')
        self.validate_required(self.body, 'body')
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = ListEcsSpecsResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class ListJobsRequest(TeaModel):
    def __init__(
        self,
        business_user_id: str = None,
        caller: str = None,
        display_name: str = None,
        end_time: str = None,
        from_all_workspaces: bool = None,
        job_type: str = None,
        order: str = None,
        page_number: int = None,
        page_size: int = None,
        pipeline_id: str = None,
        resource_id: str = None,
        show_own: bool = None,
        sort_by: str = None,
        start_time: str = None,
        status: str = None,
        tags: Dict[str, str] = None,
        workspace_id: str = None,
    ):
        self.business_user_id = business_user_id
        self.caller = caller
        self.display_name = display_name
        self.end_time = end_time
        self.from_all_workspaces = from_all_workspaces
        self.job_type = job_type
        self.order = order
        self.page_number = page_number
        self.page_size = page_size
        self.pipeline_id = pipeline_id
        self.resource_id = resource_id
        self.show_own = show_own
        self.sort_by = sort_by
        self.start_time = start_time
        self.status = status
        self.tags = tags
        self.workspace_id = workspace_id

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.business_user_id is not None:
            result['BusinessUserId'] = self.business_user_id
        if self.caller is not None:
            result['Caller'] = self.caller
        if self.display_name is not None:
            result['DisplayName'] = self.display_name
        if self.end_time is not None:
            result['EndTime'] = self.end_time
        if self.from_all_workspaces is not None:
            result['FromAllWorkspaces'] = self.from_all_workspaces
        if self.job_type is not None:
            result['JobType'] = self.job_type
        if self.order is not None:
            result['Order'] = self.order
        if self.page_number is not None:
            result['PageNumber'] = self.page_number
        if self.page_size is not None:
            result['PageSize'] = self.page_size
        if self.pipeline_id is not None:
            result['PipelineId'] = self.pipeline_id
        if self.resource_id is not None:
            result['ResourceId'] = self.resource_id
        if self.show_own is not None:
            result['ShowOwn'] = self.show_own
        if self.sort_by is not None:
            result['SortBy'] = self.sort_by
        if self.start_time is not None:
            result['StartTime'] = self.start_time
        if self.status is not None:
            result['Status'] = self.status
        if self.tags is not None:
            result['Tags'] = self.tags
        if self.workspace_id is not None:
            result['WorkspaceId'] = self.workspace_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('BusinessUserId') is not None:
            self.business_user_id = m.get('BusinessUserId')
        if m.get('Caller') is not None:
            self.caller = m.get('Caller')
        if m.get('DisplayName') is not None:
            self.display_name = m.get('DisplayName')
        if m.get('EndTime') is not None:
            self.end_time = m.get('EndTime')
        if m.get('FromAllWorkspaces') is not None:
            self.from_all_workspaces = m.get('FromAllWorkspaces')
        if m.get('JobType') is not None:
            self.job_type = m.get('JobType')
        if m.get('Order') is not None:
            self.order = m.get('Order')
        if m.get('PageNumber') is not None:
            self.page_number = m.get('PageNumber')
        if m.get('PageSize') is not None:
            self.page_size = m.get('PageSize')
        if m.get('PipelineId') is not None:
            self.pipeline_id = m.get('PipelineId')
        if m.get('ResourceId') is not None:
            self.resource_id = m.get('ResourceId')
        if m.get('ShowOwn') is not None:
            self.show_own = m.get('ShowOwn')
        if m.get('SortBy') is not None:
            self.sort_by = m.get('SortBy')
        if m.get('StartTime') is not None:
            self.start_time = m.get('StartTime')
        if m.get('Status') is not None:
            self.status = m.get('Status')
        if m.get('Tags') is not None:
            self.tags = m.get('Tags')
        if m.get('WorkspaceId') is not None:
            self.workspace_id = m.get('WorkspaceId')
        return self


class ListJobsShrinkRequest(TeaModel):
    def __init__(
        self,
        business_user_id: str = None,
        caller: str = None,
        display_name: str = None,
        end_time: str = None,
        from_all_workspaces: bool = None,
        job_type: str = None,
        order: str = None,
        page_number: int = None,
        page_size: int = None,
        pipeline_id: str = None,
        resource_id: str = None,
        show_own: bool = None,
        sort_by: str = None,
        start_time: str = None,
        status: str = None,
        tags_shrink: str = None,
        workspace_id: str = None,
    ):
        self.business_user_id = business_user_id
        self.caller = caller
        self.display_name = display_name
        self.end_time = end_time
        self.from_all_workspaces = from_all_workspaces
        self.job_type = job_type
        self.order = order
        self.page_number = page_number
        self.page_size = page_size
        self.pipeline_id = pipeline_id
        self.resource_id = resource_id
        self.show_own = show_own
        self.sort_by = sort_by
        self.start_time = start_time
        self.status = status
        self.tags_shrink = tags_shrink
        self.workspace_id = workspace_id

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.business_user_id is not None:
            result['BusinessUserId'] = self.business_user_id
        if self.caller is not None:
            result['Caller'] = self.caller
        if self.display_name is not None:
            result['DisplayName'] = self.display_name
        if self.end_time is not None:
            result['EndTime'] = self.end_time
        if self.from_all_workspaces is not None:
            result['FromAllWorkspaces'] = self.from_all_workspaces
        if self.job_type is not None:
            result['JobType'] = self.job_type
        if self.order is not None:
            result['Order'] = self.order
        if self.page_number is not None:
            result['PageNumber'] = self.page_number
        if self.page_size is not None:
            result['PageSize'] = self.page_size
        if self.pipeline_id is not None:
            result['PipelineId'] = self.pipeline_id
        if self.resource_id is not None:
            result['ResourceId'] = self.resource_id
        if self.show_own is not None:
            result['ShowOwn'] = self.show_own
        if self.sort_by is not None:
            result['SortBy'] = self.sort_by
        if self.start_time is not None:
            result['StartTime'] = self.start_time
        if self.status is not None:
            result['Status'] = self.status
        if self.tags_shrink is not None:
            result['Tags'] = self.tags_shrink
        if self.workspace_id is not None:
            result['WorkspaceId'] = self.workspace_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('BusinessUserId') is not None:
            self.business_user_id = m.get('BusinessUserId')
        if m.get('Caller') is not None:
            self.caller = m.get('Caller')
        if m.get('DisplayName') is not None:
            self.display_name = m.get('DisplayName')
        if m.get('EndTime') is not None:
            self.end_time = m.get('EndTime')
        if m.get('FromAllWorkspaces') is not None:
            self.from_all_workspaces = m.get('FromAllWorkspaces')
        if m.get('JobType') is not None:
            self.job_type = m.get('JobType')
        if m.get('Order') is not None:
            self.order = m.get('Order')
        if m.get('PageNumber') is not None:
            self.page_number = m.get('PageNumber')
        if m.get('PageSize') is not None:
            self.page_size = m.get('PageSize')
        if m.get('PipelineId') is not None:
            self.pipeline_id = m.get('PipelineId')
        if m.get('ResourceId') is not None:
            self.resource_id = m.get('ResourceId')
        if m.get('ShowOwn') is not None:
            self.show_own = m.get('ShowOwn')
        if m.get('SortBy') is not None:
            self.sort_by = m.get('SortBy')
        if m.get('StartTime') is not None:
            self.start_time = m.get('StartTime')
        if m.get('Status') is not None:
            self.status = m.get('Status')
        if m.get('Tags') is not None:
            self.tags_shrink = m.get('Tags')
        if m.get('WorkspaceId') is not None:
            self.workspace_id = m.get('WorkspaceId')
        return self


class ListJobsResponseBody(TeaModel):
    def __init__(
        self,
        jobs: List[JobItem] = None,
        request_id: str = None,
        total_count: int = None,
    ):
        self.jobs = jobs
        self.request_id = request_id
        self.total_count = total_count

    def validate(self):
        if self.jobs:
            for k in self.jobs:
                if k:
                    k.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        result['Jobs'] = []
        if self.jobs is not None:
            for k in self.jobs:
                result['Jobs'].append(k.to_map() if k else None)
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        if self.total_count is not None:
            result['TotalCount'] = self.total_count
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        self.jobs = []
        if m.get('Jobs') is not None:
            for k in m.get('Jobs'):
                temp_model = JobItem()
                self.jobs.append(temp_model.from_map(k))
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        if m.get('TotalCount') is not None:
            self.total_count = m.get('TotalCount')
        return self


class ListJobsResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: ListJobsResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        self.validate_required(self.headers, 'headers')
        self.validate_required(self.status_code, 'status_code')
        self.validate_required(self.body, 'body')
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = ListJobsResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class ListTensorboardsRequest(TeaModel):
    def __init__(
        self,
        display_name: str = None,
        end_time: str = None,
        job_id: str = None,
        order: str = None,
        page_number: int = None,
        page_size: int = None,
        sort_by: str = None,
        source_id: str = None,
        source_type: str = None,
        start_time: str = None,
        status: str = None,
        tensorboard_id: str = None,
        verbose: bool = None,
        workspace_id: str = None,
    ):
        self.display_name = display_name
        self.end_time = end_time
        self.job_id = job_id
        self.order = order
        self.page_number = page_number
        self.page_size = page_size
        self.sort_by = sort_by
        self.source_id = source_id
        self.source_type = source_type
        self.start_time = start_time
        self.status = status
        self.tensorboard_id = tensorboard_id
        self.verbose = verbose
        self.workspace_id = workspace_id

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.display_name is not None:
            result['DisplayName'] = self.display_name
        if self.end_time is not None:
            result['EndTime'] = self.end_time
        if self.job_id is not None:
            result['JobId'] = self.job_id
        if self.order is not None:
            result['Order'] = self.order
        if self.page_number is not None:
            result['PageNumber'] = self.page_number
        if self.page_size is not None:
            result['PageSize'] = self.page_size
        if self.sort_by is not None:
            result['SortBy'] = self.sort_by
        if self.source_id is not None:
            result['SourceId'] = self.source_id
        if self.source_type is not None:
            result['SourceType'] = self.source_type
        if self.start_time is not None:
            result['StartTime'] = self.start_time
        if self.status is not None:
            result['Status'] = self.status
        if self.tensorboard_id is not None:
            result['TensorboardId'] = self.tensorboard_id
        if self.verbose is not None:
            result['Verbose'] = self.verbose
        if self.workspace_id is not None:
            result['WorkspaceId'] = self.workspace_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('DisplayName') is not None:
            self.display_name = m.get('DisplayName')
        if m.get('EndTime') is not None:
            self.end_time = m.get('EndTime')
        if m.get('JobId') is not None:
            self.job_id = m.get('JobId')
        if m.get('Order') is not None:
            self.order = m.get('Order')
        if m.get('PageNumber') is not None:
            self.page_number = m.get('PageNumber')
        if m.get('PageSize') is not None:
            self.page_size = m.get('PageSize')
        if m.get('SortBy') is not None:
            self.sort_by = m.get('SortBy')
        if m.get('SourceId') is not None:
            self.source_id = m.get('SourceId')
        if m.get('SourceType') is not None:
            self.source_type = m.get('SourceType')
        if m.get('StartTime') is not None:
            self.start_time = m.get('StartTime')
        if m.get('Status') is not None:
            self.status = m.get('Status')
        if m.get('TensorboardId') is not None:
            self.tensorboard_id = m.get('TensorboardId')
        if m.get('Verbose') is not None:
            self.verbose = m.get('Verbose')
        if m.get('WorkspaceId') is not None:
            self.workspace_id = m.get('WorkspaceId')
        return self


class ListTensorboardsResponseBody(TeaModel):
    def __init__(
        self,
        request_id: str = None,
        tensorboards: List[Tensorboard] = None,
        total_count: int = None,
    ):
        self.request_id = request_id
        self.tensorboards = tensorboards
        self.total_count = total_count

    def validate(self):
        if self.tensorboards:
            for k in self.tensorboards:
                if k:
                    k.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        result['Tensorboards'] = []
        if self.tensorboards is not None:
            for k in self.tensorboards:
                result['Tensorboards'].append(k.to_map() if k else None)
        if self.total_count is not None:
            result['TotalCount'] = self.total_count
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        self.tensorboards = []
        if m.get('Tensorboards') is not None:
            for k in m.get('Tensorboards'):
                temp_model = Tensorboard()
                self.tensorboards.append(temp_model.from_map(k))
        if m.get('TotalCount') is not None:
            self.total_count = m.get('TotalCount')
        return self


class ListTensorboardsResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: ListTensorboardsResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        self.validate_required(self.headers, 'headers')
        self.validate_required(self.status_code, 'status_code')
        self.validate_required(self.body, 'body')
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = ListTensorboardsResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class StartTensorboardRequest(TeaModel):
    def __init__(
        self,
        workspace_id: str = None,
    ):
        self.workspace_id = workspace_id

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.workspace_id is not None:
            result['WorkspaceId'] = self.workspace_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('WorkspaceId') is not None:
            self.workspace_id = m.get('WorkspaceId')
        return self


class StartTensorboardResponseBody(TeaModel):
    def __init__(
        self,
        request_id: str = None,
        tensorboard_id: str = None,
    ):
        self.request_id = request_id
        self.tensorboard_id = tensorboard_id

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        if self.tensorboard_id is not None:
            result['TensorboardId'] = self.tensorboard_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        if m.get('TensorboardId') is not None:
            self.tensorboard_id = m.get('TensorboardId')
        return self


class StartTensorboardResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: StartTensorboardResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        self.validate_required(self.headers, 'headers')
        self.validate_required(self.status_code, 'status_code')
        self.validate_required(self.body, 'body')
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = StartTensorboardResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class StopJobResponseBody(TeaModel):
    def __init__(
        self,
        job_id: str = None,
        request_id: str = None,
    ):
        self.job_id = job_id
        self.request_id = request_id

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.job_id is not None:
            result['JobId'] = self.job_id
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('JobId') is not None:
            self.job_id = m.get('JobId')
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        return self


class StopJobResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: StopJobResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        self.validate_required(self.headers, 'headers')
        self.validate_required(self.status_code, 'status_code')
        self.validate_required(self.body, 'body')
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = StopJobResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class StopTensorboardRequest(TeaModel):
    def __init__(
        self,
        workspace_id: str = None,
    ):
        self.workspace_id = workspace_id

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.workspace_id is not None:
            result['WorkspaceId'] = self.workspace_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('WorkspaceId') is not None:
            self.workspace_id = m.get('WorkspaceId')
        return self


class StopTensorboardResponseBody(TeaModel):
    def __init__(
        self,
        request_id: str = None,
        tensorboard_id: str = None,
    ):
        self.request_id = request_id
        self.tensorboard_id = tensorboard_id

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        if self.tensorboard_id is not None:
            result['TensorboardId'] = self.tensorboard_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        if m.get('TensorboardId') is not None:
            self.tensorboard_id = m.get('TensorboardId')
        return self


class StopTensorboardResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: StopTensorboardResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        self.validate_required(self.headers, 'headers')
        self.validate_required(self.status_code, 'status_code')
        self.validate_required(self.body, 'body')
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = StopTensorboardResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class UpdateJobRequest(TeaModel):
    def __init__(
        self,
        priority: int = None,
    ):
        self.priority = priority

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.priority is not None:
            result['Priority'] = self.priority
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('Priority') is not None:
            self.priority = m.get('Priority')
        return self


class UpdateJobResponseBody(TeaModel):
    def __init__(
        self,
        job_id: str = None,
        request_id: str = None,
    ):
        self.job_id = job_id
        self.request_id = request_id

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.job_id is not None:
            result['JobId'] = self.job_id
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('JobId') is not None:
            self.job_id = m.get('JobId')
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        return self


class UpdateJobResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: UpdateJobResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        self.validate_required(self.headers, 'headers')
        self.validate_required(self.status_code, 'status_code')
        self.validate_required(self.body, 'body')
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = UpdateJobResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


class UpdateTensorboardRequest(TeaModel):
    def __init__(
        self,
        max_running_time_minutes: int = None,
        workspace_id: str = None,
    ):
        self.max_running_time_minutes = max_running_time_minutes
        self.workspace_id = workspace_id

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.max_running_time_minutes is not None:
            result['MaxRunningTimeMinutes'] = self.max_running_time_minutes
        if self.workspace_id is not None:
            result['WorkspaceId'] = self.workspace_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('MaxRunningTimeMinutes') is not None:
            self.max_running_time_minutes = m.get('MaxRunningTimeMinutes')
        if m.get('WorkspaceId') is not None:
            self.workspace_id = m.get('WorkspaceId')
        return self


class UpdateTensorboardResponseBody(TeaModel):
    def __init__(
        self,
        request_id: str = None,
        tensorboard_id: str = None,
    ):
        self.request_id = request_id
        self.tensorboard_id = tensorboard_id

    def validate(self):
        pass

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.request_id is not None:
            result['RequestId'] = self.request_id
        if self.tensorboard_id is not None:
            result['TensorboardId'] = self.tensorboard_id
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('RequestId') is not None:
            self.request_id = m.get('RequestId')
        if m.get('TensorboardId') is not None:
            self.tensorboard_id = m.get('TensorboardId')
        return self


class UpdateTensorboardResponse(TeaModel):
    def __init__(
        self,
        headers: Dict[str, str] = None,
        status_code: int = None,
        body: UpdateTensorboardResponseBody = None,
    ):
        self.headers = headers
        self.status_code = status_code
        self.body = body

    def validate(self):
        self.validate_required(self.headers, 'headers')
        self.validate_required(self.status_code, 'status_code')
        self.validate_required(self.body, 'body')
        if self.body:
            self.body.validate()

    def to_map(self):
        _map = super().to_map()
        if _map is not None:
            return _map

        result = dict()
        if self.headers is not None:
            result['headers'] = self.headers
        if self.status_code is not None:
            result['statusCode'] = self.status_code
        if self.body is not None:
            result['body'] = self.body.to_map()
        return result

    def from_map(self, m: dict = None):
        m = m or dict()
        if m.get('headers') is not None:
            self.headers = m.get('headers')
        if m.get('statusCode') is not None:
            self.status_code = m.get('statusCode')
        if m.get('body') is not None:
            temp_model = UpdateTensorboardResponseBody()
            self.body = temp_model.from_map(m['body'])
        return self


