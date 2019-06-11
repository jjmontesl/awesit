<?
/*
 * SiteTool
 * 2019
 */

// Config

$SITETOOL_SECRET = 'sitetool-php-secret';

// Parameters

//echo var_dump($_POST);

$secret = $_POST['secret'];
$command = $_POST['command'];

// Authenticate
// Check secret
if ($SITETOOL_SECRET != $secret) {
    http_response_code(403);
    die('Unauthorized');
}


// Route command
function route_command($command) {
    if ($command == 'file_list') {
        $path = $_POST['path'];
        return file_list($path);
    } else if ($command == 'file_backup') {
        $path = $_POST['path'];
        $files = $_POST['files'];
        return file_backup($path);
    }
    else {
        http_response_code(404);
        die('Invalid command');
    }
}

// List files in a directory recursively
function file_list($path) {

    $rii = new RecursiveIteratorIterator(new RecursiveDirectoryIterator($path));
    $files = array();

    foreach ($rii as $file) {
        if ($file->isDir()) continue;
        $ctime = gmdate('Y-m-d+H:i:s', $file->getCTime());
        $mtime = gmdate('Y-m-d+H:i:s', $file->getMTime());
        $fileinfo = array($ctime, $mtime, $file->getSize(), $file->getPathname());
        $files[] = $fileinfo;
    }

    return $files;
}

// Archive files in a directory recursively
function file_backup($path, $files) {

    $archive_path = uniqid('sitetool-file-backup-') . '.tar';

    $ar = new PharData($archive_path);
    $ar->buildFromDirectory($path);
    // TODO: Use list of files, see bottom of: https://www.php.net/manual/en/phardata.buildfromiterator.php

    $ar->compress(Phar::GZ);

    // Delete uncompressed tar
    unset($ar);
    unlink($archive_path);

    header('Content-Type: application/gzip');
    header("Content-Length: " . filesize($archive_path . ".gz"));
    $fp = fopen($archive_path . ".gz", 'rb');

    fpassthru($fp);
    fclose($fp);

    // Delete compressed tar
    unlink($archive_path . ".gz");

    exit;
}

function file_restore($path) {

    $data = $_POST['data'];

    // Write archive to disk
    $archive_path = uniqid('sitetool-file-backup-upload-') . '.tar.gz';
    file_put_contents($archive_path, $data);

    // Extract all files
    //try { } catch (Exception $e) { }
    $phar = new PharData($archive_path);
    $phar->decompress();
    $phar->extractTo($path);

    //unlink($archive_path);

}

$result = route_command($command);
echo json_encode($result); //, JSON_PRETTY_PRINT);

/*
Store articles through Joomla API:

https://forum.joomla.org/viewtopic.php?t=954108
https://docs.joomla.org/Creating_content_using_JTableContent

---


$servername = "joomladb";
$username = "root";
$password = "example";
$db = "joomla";

// Create connection
$conn = new mysqli($servername, $username, $password);

// Check connection
if ($conn->connect_error) {
    die("Connection failed: " . $conn->connect_error);
}
echo "Connected successfully";

*/


?>
