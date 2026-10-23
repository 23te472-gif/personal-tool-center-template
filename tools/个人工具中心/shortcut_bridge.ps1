param([Parameter(Mandatory=$true)][string]$RequestFile)
$ErrorActionPreference = 'Stop'
[Console]::OutputEncoding = [Text.UTF8Encoding]::new($false)
$request = Get-Content -LiteralPath $RequestFile -Raw -Encoding UTF8 | ConvertFrom-Json
$shell = New-Object -ComObject WScript.Shell
function Read-Shortcut([string]$path) {
    $item = $shell.CreateShortcut($path)
    return @{path=$path; target=$item.TargetPath; arguments=$item.Arguments; working_directory=$item.WorkingDirectory; window_style=$item.WindowStyle; hotkey=$item.Hotkey; description=$item.Description; icon=$item.IconLocation}
}
function Notify-Icon([string]$path) {
    Add-Type -TypeDefinition 'using System; using System.Runtime.InteropServices; public class IconChangeNotice { [DllImport("shell32.dll", CharSet=CharSet.Unicode)] public static extern void SHChangeNotify(uint e, uint f, string p, IntPtr q); }'
    # Wait for delivery so the worker cannot exit before Explorer processes the notice.
    [IconChangeNotice]::SHChangeNotify(0x2000,0x1005,$path,[IntPtr]::Zero)
}
try {
    switch ($request.action) {
        'dirs' { $result = @([Environment]::GetFolderPath('DesktopDirectory'), [Environment]::GetFolderPath('CommonDesktopDirectory')) | Select-Object -Unique }
        'read' { $result = Read-Shortcut $request.path }
        'refresh' { Notify-Icon $request.path; $result = @{notified=$true} }
        'read_many' {
            $result = @(foreach ($shortcutPath in $request.paths) {
                try { Read-Shortcut $shortcutPath }
                catch { @{path=$shortcutPath;error=$_.Exception.Message} }
            })
        }
        'write' {
            $before = Read-Shortcut $request.path
            if ($request.expected) {
                foreach ($key in @('target','arguments','working_directory','window_style','hotkey','description','icon')) {
                    if ($before[$key] -cne $request.expected.$key) { throw '快捷方式在操作期间发生变化，请刷新后重试。' }
                }
            }
            $item = $shell.CreateShortcut($request.path)
            $item.IconLocation = $request.icon
            $item.Save()
            $result = Read-Shortcut $request.path
            # Notify Explorer about this item only; do not clear caches or restart Explorer.
            Notify-Icon $request.path
        }
        default { throw '不支持的快捷方式操作' }
    }
    @{ok=$true;result=$result} | ConvertTo-Json -Depth 8 -Compress
} catch {
    @{ok=$false;error=$_.Exception.Message} | ConvertTo-Json -Depth 8 -Compress
    exit 1
}
