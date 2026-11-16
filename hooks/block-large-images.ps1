# PreToolUse hook for the Read tool.
# Blocks Claude from opening an image that is too big to view (which errors the
# request) and tells it to make a preview with photo-prep instead.
# Fails open: any error in this script lets the Read go through.
#
# Limits (override with environment variables):
#   CMS_IMG_MAX_MB  default 3.5   (file size Claude can safely view)
#   CMS_IMG_MAX_PX  default 2000  (longest side Claude can safely view)

try {
    $raw = [Console]::In.ReadToEnd()
    if (-not $raw) { exit 0 }
    $j = $raw | ConvertFrom-Json
    $path = $j.tool_input.file_path
    if (-not $path) { exit 0 }

    $ext = [IO.Path]::GetExtension($path).ToLower()
    $imageExts = @('.jpg', '.jpeg', '.png', '.webp', '.gif', '.bmp', '.tif', '.tiff')
    if ($imageExts -notcontains $ext) { exit 0 }
    if (-not (Test-Path -LiteralPath $path -PathType Leaf)) { exit 0 }

    $maxMB = 3.5;  if ($env:CMS_IMG_MAX_MB) { $maxMB = [double]$env:CMS_IMG_MAX_MB }
    $maxPx = 2000; if ($env:CMS_IMG_MAX_PX) { $maxPx = [int]$env:CMS_IMG_MAX_PX }

    $len = (Get-Item -LiteralPath $path).Length
    $w = 0; $h = 0
    try {
        Add-Type -AssemblyName System.Drawing
        $fs = [IO.File]::OpenRead($path)
        try {
            # validateImageData = $false reads the header only, so this is fast
            $img = [System.Drawing.Image]::FromStream($fs, $false, $false)
            $w = $img.Width; $h = $img.Height
            $img.Dispose()
        } finally { $fs.Dispose() }
    } catch { }  # unknown format (e.g. webp): fall back to the size check only

    $mb = [math]::Round($len / 1MB, 1)
    if ($len -gt ($maxMB * 1MB) -or $w -gt $maxPx -or $h -gt $maxPx) {
        $dims = if ($w -gt 0) { "${w}x${h} px, " } else { "" }
        [Console]::Error.WriteLine(
            "Blocked: '$path' is too big to view ($dims$mb MB; limit $maxPx px / $maxMB MB). " +
            "Don't open original images directly. Use the photo-prep skill: run prep_images.py with " +
            "--previews (or --previews-only for viewing only) and Read the files in _previews/ or the " +
            "_contact-sheet-*.jpg files instead.")
        exit 2
    }
    exit 0
} catch {
    exit 0
}
