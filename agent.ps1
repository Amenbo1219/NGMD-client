
# APIエンドポイント
$API_HOST = "127.0.0.1" # Please set of your API Host
$API_PORT = "8000" # Please set of your API Port
$API_PATH = "/monitor" # Please set of your API PATH

# nvidia-smi のパス
$NVIDIA_SMI = "C:\Windows\System32\nvidia-smi.exe" # Defaults NVIDIA-SMI PATH

function Get-Hostname {
    return $env:COMPUTERNAME
}

function Get-CPUUsage {
    try {
        $output = Get-WmiObject Win32_Processor | Select-Object -ExpandProperty LoadPercentage
        return [math]::Round($output, 2)
    } catch {
        Write-Host "Error fetching CPU usage: $_"
        return 0.0
    }
}

function Get-MemoryInfo {
    try {
        $mem = Get-CimInstance Win32_OperatingSystem
        $totalMemory = $mem.TotalVisibleMemorySize * 1024
        $freeMemory = $mem.FreePhysicalMemory * 1024
        $usedMemory = $totalMemory - $freeMemory
        return @{ "Used" = $usedMemory; "Total" = $totalMemory }
    } catch {
        Write-Host "Error fetching memory info: $_"
        return @{ "Used" = 0; "Total" = 0 }
    }
}

function Get-GPUMetrics {
    try {
        $output = & $NVIDIA_SMI --query-gpu=name,utilization.gpu,memory.used,memory.total --format=csv,noheader,nounits
        if ($output -match "N/A") {
            return $null
        }
        $gpuData = $output -split ", "
        return @{
            "gpu_name" = $gpuData[0].Trim()
            "gpu_usage" = [int]$gpuData[1]
            "gpu_memory_usage" = [int]$gpuData[2]
            "gpu_total_memory" = [int]$gpuData[3]
        }
    } catch {
        Write-Host "Error fetching GPU metrics: $_"
        return $null
    }
}

function Get-TopGPUUser {
    try {
        $output = & $NVIDIA_SMI --query-compute-apps=pid,used_memory --format=csv,noheader,nounits
        if (-not $output -or $output -match "No running compute processes found") {
            return ""
        }
        $processes = $output -split "`n"
        $maxMemory = 0
        $topUser = ""

        foreach ($process in $processes) {
            $data = $process -split ", "
            $procID = [int]$data[0]  # 修正: 変数名を $procID に変更
            $usedMem = [int]$data[1]

            if ($usedMem -gt $maxMemory) {
                $maxMemory = $usedMem
                try {
                    $topUser = (Get-WmiObject Win32_Process -Filter "ProcessId=$procID").GetOwner().User
                } catch {
                    Write-Host ("Error fetching user for PID {0}: {1}" -f $procID, $_)
                }
            }
        }

        return $topUser
    } catch {
        Write-Host "Error fetching GPU process data: $_"
        return ""
    }
}

function Send-Data {
    $hostname = Get-Hostname
    $cpuUsage = Get-CPUUsage
    $memoryInfo = Get-MemoryInfo
    $user = Get-TopGPUUser
    $gpuData = Get-GPUMetrics

    $systemData = @{
        "hostname" = $hostname
        "cpu_usage" = $cpuUsage
        "memory_usage" = $memoryInfo["Used"]
        "total_memory" = $memoryInfo["Total"]
        "runner" = $user
    }

    if ($gpuData) {
        $systemData += $gpuData
    }

    $jsonData = $systemData | ConvertTo-Json -Depth 3

    try {
        $uri = "http://$API_HOST`:$API_PORT$API_PATH"
        $headers = @{ "Content-Type" = "application/json" }
        Invoke-RestMethod -Uri $uri -Method Post -Body $jsonData -Headers $headers
        Write-Host "Data sent successfully"
    } catch {
        Write-Host "Error sending data: $_"
    }
}

Send-Data

