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
    } else {
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
        $fileinfo = array($file->getCTime(), $file->getMTime(), $file->getSize(), $file->getPathname());
        $files[] = $fileinfo;
    }

    return $files;
}

$result = route_command($command);
echo json_encode($result); //, JSON_PRETTY_PRINT);

/*

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
