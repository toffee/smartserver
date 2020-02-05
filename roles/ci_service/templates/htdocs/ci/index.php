<?php
require "inc/job.php";
require "inc/job_template.php";
require "config.php";

?>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<link rel="stylesheet" href="./fonts/css/animation.css">
<link rel="stylesheet" href="./fonts/css/fontello.css">
<link rel="stylesheet" href="./css/core.css">
<link rel="stylesheet" href="./css/index.css">
<script type="text/javascript">var mx = { OnScriptReady: [], OnDocReady: [] };</script>
<script src="/ressources?type=js"></script>
<script src="js/core.js"></script>
<script src="js/list.js"></script>
<script>
function initPage()
{
    mx.CIList.init(mx.$$('div.row'),mx.$("div.table"), 'div.state', 'span.state','span.runtime');
    mx.CIList.startUpdateProcess();
}
mx.OnDocReady.push( initPage );
</script>
</head>
<body>
<div class="table">
<?php
$jobs = Job::getJobs($log_folder);
foreach( $jobs as $job )
{
    echo JobTemplate::getDetails($job,true);
}
?>
</div>
</body>
</html>
