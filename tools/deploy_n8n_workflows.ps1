[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateNotNullOrEmpty()]
    [string[]]$WorkflowPath,

    [switch]$DryRun,
    [switch]$Apply,

    [ValidateNotNullOrEmpty()]
    [string]$BaseUrl = "http://127.0.0.1:5678",

    [switch]$AllowCredentialReferenceChanges,
    [switch]$AllowWorkflowReferenceChanges,
    [switch]$AllowLiveDrift,

    [string]$DeploymentStatePath = "",
    [string]$BackupRoot = ""
)

Set-StrictMode -Version Latest
$ErrorActionPreference = "Stop"

$ProjectRoot = Split-Path -Parent $PSScriptRoot
if ([string]::IsNullOrWhiteSpace($DeploymentStatePath)) {
    $DeploymentStatePath = Join-Path $ProjectRoot ".local\deployment-state.json"
}
if ([string]::IsNullOrWhiteSpace($BackupRoot)) {
    $BackupRoot = Join-Path $ProjectRoot ".local\deploy-backups"
}
$BaseUrl = $BaseUrl.TrimEnd("/")

function Write-Ok([string]$Message) {
    Write-Host "[OK] $Message" -ForegroundColor Green
}

function Write-WarningMessage([string]$Message) {
    Write-Host "[WARNING] $Message" -ForegroundColor Yellow
}

function Write-ErrorMessage([string]$Message) {
    Write-Host "[ERROR] $Message" -ForegroundColor Red
}

function Stop-Deployment([string]$Message) {
    Write-ErrorMessage $Message
    throw $Message
}

function Test-HasProperty($Object, [string]$Name) {
    return $null -ne $Object -and $null -ne $Object.PSObject.Properties[$Name]
}

function Get-StringProperty($Object, [string]$Name) {
    if (-not (Test-HasProperty $Object $Name)) {
        return ""
    }

    $Value = $Object.PSObject.Properties[$Name].Value
    if ($null -eq $Value) {
        return ""
    }

    return ([string]$Value).Trim()
}

function ConvertTo-CanonicalObject($Value) {
    if ($null -eq $Value) {
        return $null
    }

    if ($Value -is [string] -or $Value -is [char] -or $Value -is [bool] -or
        $Value -is [byte] -or $Value -is [int16] -or $Value -is [int32] -or
        $Value -is [int64] -or $Value -is [uint16] -or $Value -is [uint32] -or
        $Value -is [uint64] -or $Value -is [single] -or $Value -is [double] -or
        $Value -is [decimal] -or $Value -is [datetime]) {
        return $Value
    }

    if ($Value -is [System.Collections.IDictionary]) {
        $Result = [ordered]@{}
        foreach ($Key in @($Value.Keys | Sort-Object)) {
            $Result[[string]$Key] = ConvertTo-CanonicalObject $Value[$Key]
        }
        return $Result
    }

    if ($Value -is [System.Collections.IEnumerable]) {
        $Items = @()
        foreach ($Item in $Value) {
            $Items += ,(ConvertTo-CanonicalObject $Item)
        }
        return $Items
    }

    $Properties = @($Value.PSObject.Properties | Where-Object {
        $_.MemberType -in @("NoteProperty", "Property")
    } | Sort-Object Name)

    if ($Properties.Count -gt 0) {
        $Result = [ordered]@{}
        foreach ($Property in $Properties) {
            $Result[$Property.Name] = ConvertTo-CanonicalObject $Property.Value
        }
        return $Result
    }

    return $Value
}

function ConvertTo-CanonicalJson($Value) {
    return (ConvertTo-CanonicalObject $Value | ConvertTo-Json -Depth 100 -Compress)
}

function Get-WritableWorkflowSettings($Settings) {
    $WritableSettings = [ordered]@{}
    $AllowedSettings = @(
        "saveExecutionProgress",
        "saveManualExecutions",
        "saveDataErrorExecution",
        "saveDataSuccessExecution",
        "executionTimeout",
        "errorWorkflow",
        "timezone",
        "executionOrder",
        "callerPolicy",
        "callerIds",
        "timeSavedPerExecution",
        "redactionPolicy",
        "availableInMCP",
        "customTelemetryTags"
    )

    foreach ($SettingName in $AllowedSettings) {
        if (Test-HasProperty $Settings $SettingName) {
            $WritableSettings[$SettingName] = $Settings.PSObject.Properties[$SettingName].Value
        }
    }

    return [pscustomobject]$WritableSettings
}

function Get-WritableWorkflowPayload($Workflow) {
    $Payload = [ordered]@{
        name = $Workflow.name
        nodes = $Workflow.nodes
        connections = $Workflow.connections
        settings = Get-WritableWorkflowSettings $Workflow.settings
    }

    foreach ($OptionalField in @("description", "staticData", "pinData", "nodeGroups")) {
        if (Test-HasProperty $Workflow $OptionalField) {
            $Payload[$OptionalField] = $Workflow.PSObject.Properties[$OptionalField].Value
        }
    }

    return [pscustomobject]$Payload
}

function Get-ComparableLivePayload($LiveWorkflow, $SourcePayload) {
    $Payload = [ordered]@{
        name = $LiveWorkflow.name
        nodes = $LiveWorkflow.nodes
        connections = $LiveWorkflow.connections
        settings = Get-WritableWorkflowSettings $LiveWorkflow.settings
    }

    foreach ($OptionalField in @("description", "staticData", "pinData", "nodeGroups")) {
        if (Test-HasProperty $SourcePayload $OptionalField) {
            $Value = $null
            if (Test-HasProperty $LiveWorkflow $OptionalField) {
                $Value = $LiveWorkflow.PSObject.Properties[$OptionalField].Value
            }
            $Payload[$OptionalField] = $Value
        }
    }

    return [pscustomobject]$Payload
}

function Get-CredentialReferences($Workflow) {
    $References = @()

    foreach ($Node in @($Workflow.nodes)) {
        if (-not (Test-HasProperty $Node "credentials") -or $null -eq $Node.credentials) {
            continue
        }

        $NodeId = Get-StringProperty $Node "id"
        $NodeName = Get-StringProperty $Node "name"

        foreach ($CredentialProperty in @($Node.credentials.PSObject.Properties | Sort-Object Name)) {
            $Credential = $CredentialProperty.Value
            $CredentialId = Get-StringProperty $Credential "id"
            $CredentialName = Get-StringProperty $Credential "name"
            $CredentialType = $CredentialProperty.Name
            $References += [pscustomobject]@{
                identity = "$NodeId|$CredentialType|$CredentialId|$CredentialName"
                nodeId = $NodeId
                nodeName = $NodeName
                credentialType = $CredentialType
                credentialId = $CredentialId
                credentialName = $CredentialName
            }
        }
    }

    return @($References | Sort-Object -Property identity -Unique)
}

function Format-CredentialReference($Reference) {
    return (
        "node id '$($Reference.nodeId)' " +
        "(node name '$($Reference.nodeName)'), " +
        "credential type '$($Reference.credentialType)', " +
        "credential id '$($Reference.credentialId)', " +
        "credential name '$($Reference.credentialName)'"
    )
}

function Assert-CredentialReferences(
    [string]$Label,
    [object[]]$SourceValues,
    [object[]]$LiveValues,
    [bool]$AllowChanges
) {
    $Separator = [string][char]31
    $SourceIdentities = @($SourceValues | ForEach-Object { $_.identity } | Sort-Object -Unique)
    $LiveIdentities = @($LiveValues | ForEach-Object { $_.identity } | Sort-Object -Unique)
    $SourceSet = $SourceIdentities -join $Separator
    $LiveSet = $LiveIdentities -join $Separator

    if ($SourceSet -eq $LiveSet) {
        Write-Ok "$Label unchanged"
        return
    }

    if ($AllowChanges) {
        Write-WarningMessage "$Label differ; explicitly allowed by command-line switch"
        return
    }

    $SourceDisplay = @($SourceValues | ForEach-Object { Format-CredentialReference $_ })
    $LiveDisplay = @($LiveValues | ForEach-Object { Format-CredentialReference $_ })
    Write-WarningMessage "Source references: $(if ($SourceDisplay.Count) { $SourceDisplay -join '; ' } else { '<none>' })"
    Write-WarningMessage "Live references: $(if ($LiveDisplay.Count) { $LiveDisplay -join '; ' } else { '<none>' })"
    Stop-Deployment "$Label differ from the live workflow. Review the credential references."
}

function Get-WorkflowCallReferences($Workflow) {
    $References = @()

    foreach ($Node in @($Workflow.nodes)) {
        if ((Get-StringProperty $Node "type") -ne "n8n-nodes-base.executeWorkflow") {
            continue
        }

        if (-not (Test-HasProperty $Node.parameters "workflowId")) {
            continue
        }

        $RawTarget = $Node.parameters.workflowId
        $TargetId = ""
        if ($RawTarget -is [string]) {
            $TargetId = $RawTarget.Trim()
        }
        elseif ($null -ne $RawTarget -and (Test-HasProperty $RawTarget "value")) {
            $TargetId = ([string]$RawTarget.value).Trim()
        }

        if ($TargetId -and -not $TargetId.StartsWith("=")) {
            $References += "$(Get-StringProperty $Node 'id')|$(Get-StringProperty $Node 'name')|$TargetId"
        }
    }

    return @($References | Sort-Object -Unique)
}

function Get-TargetIdsFromReferences([string[]]$References) {
    $Targets = @()
    foreach ($Reference in @($References)) {
        $Parts = $Reference.Split("|")
        if ($Parts.Count -ge 3 -and $Parts[2]) {
            $Targets += $Parts[2]
        }
    }
    return @($Targets | Sort-Object -Unique)
}

function Assert-EqualSets(
    [string]$Label,
    [string[]]$SourceValues,
    [string[]]$LiveValues,
    [bool]$AllowChanges
) {
    $Separator = [string][char]31
    $SourceSet = (@($SourceValues | Sort-Object -Unique) -join $Separator)
    $LiveSet = (@($LiveValues | Sort-Object -Unique) -join $Separator)

    if ($SourceSet -eq $LiveSet) {
        Write-Ok "$Label unchanged"
        return
    }

    if ($AllowChanges) {
        Write-WarningMessage "$Label differ; explicitly allowed by command-line switch"
        return
    }

    Write-WarningMessage "Source references: $(if ($SourceValues.Count) { $SourceValues -join '; ' } else { '<none>' })"
    Write-WarningMessage "Live references: $(if ($LiveValues.Count) { $LiveValues -join '; ' } else { '<none>' })"
    Stop-Deployment "$Label differ from the live workflow. Review the references or use the explicit allow-change switch."
}

function Assert-WorkflowStructure($Workflow, [string]$Path) {
    $WorkflowId = Get-StringProperty $Workflow "id"
    $WorkflowName = Get-StringProperty $Workflow "name"

    if (-not $WorkflowId) {
        Stop-Deployment "Workflow JSON has no id: $Path"
    }
    if (-not $WorkflowName) {
        Stop-Deployment "Workflow JSON has no name: $Path"
    }
    if (-not (Test-HasProperty $Workflow "nodes") -or $null -eq $Workflow.nodes) {
        Stop-Deployment "Workflow JSON has no nodes array: $Path"
    }
    if (-not (Test-HasProperty $Workflow "connections") -or $null -eq $Workflow.connections) {
        Stop-Deployment "Workflow JSON has no connections object: $Path"
    }
    if (-not (Test-HasProperty $Workflow "settings") -or $null -eq $Workflow.settings) {
        Stop-Deployment "Workflow JSON has no settings object: $Path"
    }

    $NodeNames = @{}
    $NodeIds = @{}
    foreach ($Node in @($Workflow.nodes)) {
        $NodeName = Get-StringProperty $Node "name"
        $NodeType = Get-StringProperty $Node "type"
        $NodeId = Get-StringProperty $Node "id"

        if (-not $NodeName -or -not $NodeType) {
            Stop-Deployment "A node is missing its name or type in workflow '$WorkflowName'."
        }
        if ($NodeNames.ContainsKey($NodeName)) {
            Stop-Deployment "Duplicate node name '$NodeName' in workflow '$WorkflowName'."
        }
        $NodeNames[$NodeName] = $true

        if ($NodeId) {
            if ($NodeIds.ContainsKey($NodeId)) {
                Stop-Deployment "Duplicate node id '$NodeId' in workflow '$WorkflowName'."
            }
            $NodeIds[$NodeId] = $true
        }
    }

    foreach ($ConnectionProperty in @($Workflow.connections.PSObject.Properties)) {
        if (-not $NodeNames.ContainsKey($ConnectionProperty.Name)) {
            Stop-Deployment "Connection source '$($ConnectionProperty.Name)' is not a workflow node in '$WorkflowName'."
        }

        $ConnectionGroups = $ConnectionProperty.Value
        if ($null -eq $ConnectionGroups) {
            continue
        }

        foreach ($OutputProperty in @($ConnectionGroups.PSObject.Properties)) {
            foreach ($Branch in @($OutputProperty.Value)) {
                foreach ($Edge in @($Branch)) {
                    if ($null -eq $Edge) {
                        continue
                    }
                    $TargetName = Get-StringProperty $Edge "node"
                    if (-not $TargetName -or -not $NodeNames.ContainsKey($TargetName)) {
                        Stop-Deployment "Connection target '$TargetName' is invalid in workflow '$WorkflowName'."
                    }
                }
            }
        }
    }

    Write-Ok "Workflow JSON valid: $WorkflowName"
}

function Invoke-N8nApi(
    [ValidateSet("GET", "PUT")]
    [string]$Method,
    [string]$Path,
    $Body = $null
) {
    $Uri = "$BaseUrl$Path"
    $Parameters = @{
        Method = $Method
        Uri = $Uri
        Headers = $script:ApiHeaders
        ErrorAction = "Stop"
    }

    if ($Method -eq "PUT") {
        $Parameters["ContentType"] = "application/json; charset=utf-8"
        $JsonBody = $Body | ConvertTo-Json -Depth 100 -Compress
        $Parameters["Body"] = [System.Text.Encoding]::UTF8.GetBytes($JsonBody)
    }

    try {
        return Invoke-RestMethod @Parameters
    }
    catch {
        $ApiErrorRecord = $_
        $Status = ""
        if ($null -ne $ApiErrorRecord.Exception.Response) {
            try {
                $Status = " HTTP $([int]$ApiErrorRecord.Exception.Response.StatusCode)"
            }
            catch {
                $Status = ""
            }
        }
        $ApiDetail = ""
        $ResponseBody = ""
        if ($null -ne $ApiErrorRecord.ErrorDetails -and
            -not [string]::IsNullOrWhiteSpace($ApiErrorRecord.ErrorDetails.Message)) {
            $ResponseBody = $ApiErrorRecord.ErrorDetails.Message
        }
        elseif ($null -ne $ApiErrorRecord.Exception.Response) {
            try {
                $ResponseStream = $ApiErrorRecord.Exception.Response.GetResponseStream()
                if ($null -ne $ResponseStream) {
                    $Reader = New-Object System.IO.StreamReader($ResponseStream)
                    try {
                        $ResponseBody = $Reader.ReadToEnd()
                    }
                    finally {
                        $Reader.Dispose()
                    }
                }
            }
            catch {
                $ResponseBody = ""
            }
        }

        if (-not [string]::IsNullOrWhiteSpace($ResponseBody)) {
            try {
                $ErrorBody = $ResponseBody | ConvertFrom-Json
                $SafeMessages = @()
                foreach ($PropertyName in @("message", "error")) {
                    if (Test-HasProperty $ErrorBody $PropertyName) {
                        $Value = $ErrorBody.PSObject.Properties[$PropertyName].Value
                        if ($Value -is [string] -and -not [string]::IsNullOrWhiteSpace($Value)) {
                            $SafeMessages += $Value.Trim()
                        }
                    }
                }
                if (Test-HasProperty $ErrorBody "errors") {
                    foreach ($Entry in @($ErrorBody.errors)) {
                        $EntryMessage = Get-StringProperty $Entry "message"
                        $EntryPath = Get-StringProperty $Entry "path"
                        if ($EntryMessage) {
                            $SafeMessages += $(if ($EntryPath) { "$EntryPath`: $EntryMessage" } else { $EntryMessage })
                        }
                    }
                }
                if ($SafeMessages.Count -gt 0) {
                    $ApiDetail = ($SafeMessages | Select-Object -Unique) -join "; "
                }
            }
            catch {
                # Do not print an unstructured response body because it could echo request data.
                $ApiDetail = ""
            }
        }

        if ($ApiDetail) {
            if (-not [string]::IsNullOrWhiteSpace($ApiKey)) {
                $ApiDetail = $ApiDetail.Replace($ApiKey, "<redacted>")
            }
            if ($ApiDetail.Length -gt 2000) {
                $ApiDetail = $ApiDetail.Substring(0, 2000) + "..."
            }
            throw "n8n API $Method $Path failed.$Status $($ApiErrorRecord.Exception.Message) API response: $ApiDetail"
        }
        throw "n8n API $Method $Path failed.$Status $($ApiErrorRecord.Exception.Message)"
    }
}

function Get-LiveWorkflow([string]$WorkflowId) {
    $EncodedId = [uri]::EscapeDataString($WorkflowId)
    return Invoke-N8nApi -Method GET -Path "/api/v1/workflows/$EncodedId"
}

function Read-DeploymentState {
    if (-not (Test-Path -LiteralPath $DeploymentStatePath -PathType Leaf)) {
        return [pscustomobject]@{
            schemaVersion = 1
            workflows = @()
        }
    }

    try {
        $State = Get-Content -LiteralPath $DeploymentStatePath -Raw -Encoding UTF8 | ConvertFrom-Json
    }
    catch {
        Stop-Deployment "Deployment state JSON is invalid: $DeploymentStatePath"
    }

    if (-not (Test-HasProperty $State "workflows")) {
        Stop-Deployment "Deployment state is missing the workflows array: $DeploymentStatePath"
    }

    return $State
}

function Save-DeploymentState($State) {
    $Directory = Split-Path -Parent $DeploymentStatePath
    if (-not (Test-Path -LiteralPath $Directory -PathType Container)) {
        New-Item -ItemType Directory -Path $Directory -Force | Out-Null
    }

    $TemporaryPath = "$DeploymentStatePath.tmp"
    $State | ConvertTo-Json -Depth 20 | Set-Content -LiteralPath $TemporaryPath -Encoding UTF8
    Move-Item -LiteralPath $TemporaryPath -Destination $DeploymentStatePath -Force
}

function Get-StateEntry($State, [string]$WorkflowId) {
    return @($State.workflows | Where-Object { $_.id -eq $WorkflowId }) | Select-Object -First 1
}

function Set-StateEntry($State, $Entry) {
    $Remaining = @($State.workflows | Where-Object { $_.id -ne $Entry.id })
    $State.workflows = @($Remaining + $Entry | Sort-Object id)
}

if (($DryRun -and $Apply) -or (-not $DryRun -and -not $Apply)) {
    Write-Host ""
    Write-Host "USAGE:" -ForegroundColor Cyan
    Write-Host "  .\tools\deploy_n8n_workflows.ps1 -WorkflowPath <file-or-files> -DryRun"
    Write-Host "  .\tools\deploy_n8n_workflows.ps1 -WorkflowPath <file-or-files> -Apply"
    Write-Host ""
    Stop-Deployment "Specify exactly one of -DryRun or -Apply. No live changes were made."
}

$ApiKey = [Environment]::GetEnvironmentVariable("PROJECT_E_N8N_API_KEY", "Process")
if ([string]::IsNullOrWhiteSpace($ApiKey)) {
    Stop-Deployment "PROJECT_E_N8N_API_KEY is not set in the current process. No live changes were made."
}

$script:ApiHeaders = @{
    "X-N8N-API-KEY" = $ApiKey
}

Write-Host ""
Write-Host "Project-E n8n deployment preflight" -ForegroundColor Cyan
Write-Host "Mode: $(if ($DryRun) { 'DRY RUN' } else { 'APPLY' })"
Write-Host "Target: $BaseUrl"
Write-Host ""

try {
    $Reachability = Invoke-N8nApi -Method GET -Path "/api/v1/workflows?limit=1&excludePinnedData=true"
    Write-Ok "n8n reachable"
    Write-Ok "API authentication successful"
}
catch {
    Stop-Deployment $_.Exception.Message
}

$State = Read-DeploymentState
$Selected = @()
$SelectedIds = @{}

foreach ($RequestedPath in $WorkflowPath) {
    try {
        $ResolvedPath = (Resolve-Path -LiteralPath $RequestedPath -ErrorAction Stop).Path
    }
    catch {
        Stop-Deployment "Workflow file not found: $RequestedPath"
    }

    try {
        $RawJson = Get-Content -LiteralPath $ResolvedPath -Raw -Encoding UTF8
        $Workflow = $RawJson | ConvertFrom-Json
    }
    catch {
        Stop-Deployment "Invalid workflow JSON: $ResolvedPath"
    }

    Assert-WorkflowStructure $Workflow $ResolvedPath

    $WorkflowId = Get-StringProperty $Workflow "id"
    if ($SelectedIds.ContainsKey($WorkflowId)) {
        Stop-Deployment "Duplicate selected workflow id '$WorkflowId'."
    }
    $SelectedIds[$WorkflowId] = $true

    $Selected += [pscustomobject]@{
        path = $ResolvedPath
        source = $Workflow
        sourceHash = (Get-FileHash -LiteralPath $ResolvedPath -Algorithm SHA256).Hash.ToLowerInvariant()
        id = $WorkflowId
        name = Get-StringProperty $Workflow "name"
        payload = Get-WritableWorkflowPayload $Workflow
        credentialReferences = @(Get-CredentialReferences $Workflow)
        workflowReferences = @(Get-WorkflowCallReferences $Workflow)
        live = $null
        definitionChanged = $false
    }
}

$LiveCache = @{}
foreach ($Item in $Selected) {
    try {
        $Live = Get-LiveWorkflow $Item.id
    }
    catch {
        Stop-Deployment "Live workflow '$($Item.id)' was not found or could not be read. $($_.Exception.Message)"
    }

    $LiveCache[$Item.id] = $Live
    $Item.live = $Live
    Write-Ok "Workflow found: $($Item.name) [$($Item.id)]"

    if ((Get-StringProperty $Live "id") -ne $Item.id) {
        Stop-Deployment "Live workflow ID does not match source ID '$($Item.id)'."
    }
    Write-Ok "Workflow ID matches: $($Item.id)"

    if ((Get-StringProperty $Live "name") -ne $Item.name) {
        Stop-Deployment "Workflow name mismatch for '$($Item.id)': source '$($Item.name)', live '$(Get-StringProperty $Live 'name')'."
    }
    Write-Ok "Workflow name matches: $($Item.name)"

    Assert-CredentialReferences `
        "Credential references for $($Item.name)" `
        $Item.credentialReferences `
        @(Get-CredentialReferences $Live) `
        $AllowCredentialReferenceChanges.IsPresent

    Assert-EqualSets `
        "Workflow-call references for $($Item.name)" `
        $Item.workflowReferences `
        @(Get-WorkflowCallReferences $Live) `
        $AllowWorkflowReferenceChanges.IsPresent

    $StateEntry = Get-StateEntry $State $Item.id
    $LiveVersionId = Get-StringProperty $Live "versionId"
    if ($null -ne $StateEntry) {
        $RecordedLiveVersionId = Get-StringProperty $StateEntry "liveVersionId"
        if (-not $RecordedLiveVersionId) {
            Stop-Deployment "Deployment-state entry for $($Item.name) has no liveVersionId. Repair or remove the invalid state entry before deploying."
        }

        if ($RecordedLiveVersionId -ne $LiveVersionId) {
            if ($AllowLiveDrift) {
                Write-WarningMessage "Live version drift explicitly allowed for $($Item.name)"
            }
            else {
                Stop-Deployment "Live version drift detected for $($Item.name). Expected '$RecordedLiveVersionId', found '$LiveVersionId'."
            }
        }
        else {
            Write-Ok "No live version drift: $($Item.name)"
        }
    }
    else {
        Write-WarningMessage (
            "No deployment-state entry exists for $($Item.name). " +
            "Treating this as its first managed deployment; source export versionId is historical metadata, " +
            "so live-version drift cannot be established until a successful Apply records the resulting versionId."
        )
    }

    $SourceDefinition = ConvertTo-CanonicalJson $Item.payload
    $LiveDefinition = ConvertTo-CanonicalJson (Get-ComparableLivePayload $Live $Item.payload)
    $Item.definitionChanged = $SourceDefinition -ne $LiveDefinition
    if ($Item.definitionChanged) {
        Write-Host "[CHANGE] $($Item.name) would be updated" -ForegroundColor Cyan
    }
    else {
        Write-Ok "Live writable definition already matches source: $($Item.name)"
    }
}

$AllReferencedTargets = @()
foreach ($Item in $Selected) {
    $AllReferencedTargets += Get-TargetIdsFromReferences $Item.workflowReferences
}

foreach ($TargetId in @($AllReferencedTargets | Sort-Object -Unique)) {
    if ($LiveCache.ContainsKey($TargetId)) {
        continue
    }
    try {
        $LiveCache[$TargetId] = Get-LiveWorkflow $TargetId
        Write-Ok "Referenced workflow target exists: $TargetId"
    }
    catch {
        Stop-Deployment "Referenced workflow target does not exist or is inaccessible: $TargetId"
    }
}

Write-Host ""
if ($DryRun) {
    Write-Host "WOULD DEPLOY IN THIS ORDER:" -ForegroundColor Cyan
    foreach ($Item in $Selected) {
        $Action = if ($Item.definitionChanged) { "UPDATE" } else { "NO-OP" }
        Write-Host "  [$Action] $($Item.name) [$($Item.id)]"
    }
    Write-Host ""
    Write-Host "NO LIVE CHANGES MADE." -ForegroundColor Green
    Write-Host "No backups or deployment-state changes were created."
    exit 0
}

$Timestamp = (Get-Date).ToUniversalTime().ToString("yyyyMMddTHHmmssZ")
$BackupDirectory = Join-Path $BackupRoot $Timestamp
$Deployed = @()
$Touched = @()
$Pending = @($Selected)

try {
    foreach ($Item in $Selected) {
        $Pending = @($Pending | Where-Object { $_.id -ne $Item.id })

        if (-not $Item.definitionChanged) {
            Write-Ok "No PUT required; definition already current: $($Item.name)"
            $Deployed += [pscustomobject]@{
                item = $Item
                live = $Item.live
                changed = $false
                backupPath = $null
            }
            continue
        }

        if (-not (Test-Path -LiteralPath $BackupDirectory -PathType Container)) {
            New-Item -ItemType Directory -Path $BackupDirectory -Force | Out-Null
        }

        $BackupPath = Join-Path $BackupDirectory "$($Item.id).json"
        $Item.live | ConvertTo-Json -Depth 100 | Set-Content -LiteralPath $BackupPath -Encoding UTF8
        Write-Ok "Pre-deployment backup saved: $BackupPath"

        $BeforeVersionId = Get-StringProperty $Item.live "versionId"
        $BeforeActive = [bool]$Item.live.active
        $BeforeActiveVersionId = Get-StringProperty $Item.live "activeVersionId"

        $EncodedId = [uri]::EscapeDataString($Item.id)
        $null = Invoke-N8nApi -Method PUT -Path "/api/v1/workflows/$EncodedId" -Body $Item.payload
        $Touched += [pscustomobject]@{
            item = $Item
            backupPath = $BackupPath
        }

        $After = Get-LiveWorkflow $Item.id
        if ((Get-StringProperty $After "id") -ne $Item.id) {
            Stop-Deployment "Post-deployment workflow ID verification failed for $($Item.name)."
        }
        if ((Get-StringProperty $After "name") -ne $Item.name) {
            Stop-Deployment "Post-deployment workflow name verification failed for $($Item.name)."
        }

        $AfterDefinition = ConvertTo-CanonicalJson (Get-ComparableLivePayload $After $Item.payload)
        $SourceDefinition = ConvertTo-CanonicalJson $Item.payload
        if ($AfterDefinition -ne $SourceDefinition) {
            Stop-Deployment "Post-deployment writable definition does not match source for $($Item.name)."
        }

        Assert-CredentialReferences `
            "Post-deployment credential references for $($Item.name)" `
            $Item.credentialReferences `
            @(Get-CredentialReferences $After) `
            $false

        Assert-EqualSets `
            "Post-deployment workflow-call references for $($Item.name)" `
            $Item.workflowReferences `
            @(Get-WorkflowCallReferences $After) `
            $false

        $AfterActive = [bool]$After.active
        if ($AfterActive -ne $BeforeActive) {
            Stop-Deployment "Active state changed unexpectedly for $($Item.name)."
        }

        $AfterVersionId = Get-StringProperty $After "versionId"
        if (-not $AfterVersionId -or $AfterVersionId -eq $BeforeVersionId) {
            Stop-Deployment "Workflow versionId did not change after updating $($Item.name)."
        }

        if ($BeforeActive) {
            $AfterActiveVersionId = Get-StringProperty $After "activeVersionId"
            if (-not $AfterActiveVersionId) {
                Stop-Deployment "Previously active workflow is no longer published: $($Item.name)."
            }
            if ($AfterActiveVersionId -ne $AfterVersionId) {
                Stop-Deployment "Published version does not match the deployed version for $($Item.name)."
            }
        }
        elseif ($BeforeActiveVersionId -and -not $After.active) {
            Write-WarningMessage "Inactive workflow retained a prior activeVersionId metadata value: $($Item.name)"
        }

        Write-Ok "$($Item.name) deployed"
        Write-Ok "Workflow ID preserved"
        Write-Ok "Active state preserved"
        Write-Ok "Definition verified"

        $Deployed += [pscustomobject]@{
            item = $Item
            live = $After
            changed = $true
            backupPath = $BackupPath
        }
    }
}
catch {
    Write-Host ""
    Write-ErrorMessage "Deployment stopped: $($_.Exception.Message)"
    Write-Host ""
    Write-Host "WORKFLOWS ALREADY UPDATED:" -ForegroundColor Yellow
    if ($Touched.Count -eq 0) {
        Write-Host "  None"
    }
    else {
        foreach ($Entry in $Touched) {
            Write-Host "  $($Entry.item.name) [$($Entry.item.id)]"
        }
    }

    Write-Host "WORKFLOWS NOT YET TOUCHED:" -ForegroundColor Yellow
    if ($Pending.Count -eq 0) {
        Write-Host "  None"
    }
    else {
        foreach ($Entry in $Pending) {
            Write-Host "  $($Entry.name) [$($Entry.id)]"
        }
    }

    if ($Touched.Count -gt 0) {
        Write-Host "BACKUP DIRECTORY: $BackupDirectory" -ForegroundColor Yellow
        Write-Host "SAFE ROLLBACK ORDER:" -ForegroundColor Yellow
        $RollbackPaths = @()
        for ($Index = $Touched.Count - 1; $Index -ge 0; $Index--) {
            $Entry = $Touched[$Index]
            $RollbackPaths += $Entry.backupPath
            Write-Host "  $($Entry.item.name) <- $($Entry.backupPath)"
        }
        Write-Host "ROLLBACK COMMAND (review before running):" -ForegroundColor Yellow
        Write-Host ("& '$($PSCommandPath.Replace("'", "''"))' -WorkflowPath @(")
        foreach ($RollbackPath in $RollbackPaths) {
            Write-Host "  '$($RollbackPath.Replace("'", "''"))'"
        }
        Write-Host ") -Apply -AllowLiveDrift -BaseUrl '$($BaseUrl.Replace("'", "''"))'"
        Write-Host "Review the failure before running rollback; rollback is never automatic."
    }

    exit 1
}

$DeploymentTimestamp = (Get-Date).ToUniversalTime().ToString("o")
foreach ($Result in $Deployed) {
    $FinalLive = $Result.live
    Set-StateEntry $State ([pscustomobject]@{
        id = $Result.item.id
        name = $Result.item.name
        sourceSha256 = $Result.item.sourceHash
        liveVersionId = Get-StringProperty $FinalLive "versionId"
        active = [bool]$FinalLive.active
        activeVersionId = Get-StringProperty $FinalLive "activeVersionId"
        deployedAtUtc = $DeploymentTimestamp
    })
}
Save-DeploymentState $State
Write-Ok "Deployment state updated: $DeploymentStatePath"

Write-Host ""
Write-Host "SUCCESS" -ForegroundColor Green
Write-Host "All selected Project-E workflows deployed and verified."
if (Test-Path -LiteralPath $BackupDirectory -PathType Container) {
    Write-Host "Backups: $BackupDirectory"
}
Write-Host ""
Write-Host "NEXT REQUIRED STEP:" -ForegroundColor Cyan
Write-Host "Run a real Project-E smoke test before committing."
