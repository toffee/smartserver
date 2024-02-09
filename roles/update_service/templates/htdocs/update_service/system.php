<?php
require "../shared/libs/i18n.php";
require "../shared/libs/ressources.php";

require "inc/job.php";

require "config.php";
?>
<html>
<head>
<meta name="viewport" content="width=device-width, initial-scale=1">
<?php echo Ressources::getModules(["/shared/mod/websocket/", "/shared/mod/logfile/","/update_service/"]); ?>
<script>
    mx.UNCore = (function( ret ) {
        var updateJobStarted = false;
        
        var systemUpdatesCount = 0;
        var smartserverChangesCount = 0;
        var systemUpdatesHash = "";
        var smartserverChangesHash = "";
        
        var last_data_modified = null;
        var hasEncryptedVault = false;
        var deploymentTags = [];

        var refreshDaemonStateTimer = 0;
        
        var daemonApiUrl = mx.Host.getBase() + '../api/'; 

        var daemonNeedsRestart = false;
        var job_state = {}

        function processRunningJobDetails(data)
        {
            job_state = {...job_state, ...data};

            let job_is_running = job_state["job"] != null;
            let job_running_type = job_state["type"];
            let job_cmd_type = job_state["job"];
            let job_started = job_state["started"];

            var msg = "";
            var currentRunningStateElement = mx.$("#currentRunningState");
            var currentRunningActionsElement = mx.$("#currentRunningActions");

            if( job_is_running )
            {
                var logfile = job_state["logfile"];
                if( logfile && job_started)
                {
                    var logfile_name = logfile.substring(0,logfile.length - 4);
                    var logfile_parts = logfile_name.split("-");

                    action_msg_1 = "<span class=\"detailView\" onClick=\"mx.UpdateServiceActions.openDetails(this,'" + logfile_parts[0] + "','" + logfile_parts[3] + "','" + logfile_parts[4] + "')\">";
                    action_msg_2 = "</span>";

                    var runtime = Math.round( ( (new Date()).getTime() - Date.parse(job_started) ) / 1000 );

                    msg = mx.UpdateServiceTemplates.getActiveServiceJobName(job_cmd_type).fill({"1": action_msg_1, "2": action_msg_2, "3": runtime, "4": mx.I18N.get( runtime == 1 ? "second" : "seconds" ) });

                    if( job_state["killable"] )
                    {
                        currentRunningActionsElement.style.display= "block";
                    }
                    else
                    {
                        currentRunningActionsElement.style.display= "";
                        currentRunningActionsElement.querySelector(".button").classList.remove("disabled");
                    }
                }
                else
                {
                    msg = "<span class=\"icon-attention yellow\"></span> " + mx.UpdateServiceTemplates.getActiveManuellJobName(job_cmd_type);
                    currentRunningActionsElement.style.display= ""
                }
            }
            else
            {
                currentRunningActionsElement.style.display="";
                currentRunningActionsElement.querySelector(".button").classList.remove("disabled");

                if( job_state["workflow"] )
                {
                    switch (job_state["workflow"]) {
                        case 'killed':
                            msg = mx.I18N.get("Last process was killed")
                            break;
                        case 'stopped':
                            msg = mx.I18N.get("Last process was stopped")
                            break;
                        default:
                            let reasons = job_state["workflow"].split(",");
                            if( reasons.indexOf("wrong_system_update_hash") != -1 && reasons.indexOf("wrong_smartserver_update_hash") != -1 )
                            {
                                msg = mx.I18N.get("Last process was stopped, because of new system and smartserver updates");
                            }
                            else if( reasons.indexOf("wrong_system_update_hash") != -1 )
                            {
                                msg = mx.I18N.get("Last process was stopped, because of new system updates");
                            }
                            else if( reasons.indexOf("wrong_smartserver_update_hash") != -1 )
                            {
                                msg = mx.I18N.get("Last process was stopped, because of new smartserver updates");
                            }
                            break;
                    }

                    msg = "<span class=\"icon-attention red\"></span> " + msg;
                }
                else
                {
                    msg = mx.I18N.get("No update process is running");
                }
            }

            if( currentRunningStateElement.innerHTML != msg )  currentRunningStateElement.innerHTML = msg;

            if( mx.UpdateServiceActions.getDialog() != null )
            {
                let dialog = mx.UpdateServiceActions.getDialog();
                if( dialog.getId() != "killProcess" )
                {
                    if( job_is_running )
                    {
                        let msg = mx.I18N.get("'{}' disabled, because of a running job");
                        msg = msg.fill(dialog.getElement(".continue").innerHTML);
                        dialog.setInfo(msg);
                        dialog.setActionDisabled(".continue",true);
                    }
                    else
                    {
                        dialog.setInfo("");
                        dialog.setActionDisabled(".continue",false);
                    }
                }
            }

            if( job_is_running )
            {
                mx.UpdateServiceHelper.setExclusiveButtonsState(false, job_running_type == "manual" ? null: "kill");
            }
            else
            {
                if( daemonNeedsRestart )
                {
                    mx.UpdateServiceHelper.setExclusiveButtonsState(false, "restart");
                }
                else
                {
                    mx.UpdateServiceHelper.setExclusiveButtonsState(true, null );
                }
            }
        }

        function processDataNew(data)
        {
            if( "update_server_needs_restart" in data )
            {
                daemonNeedsRestart = data["update_server_needs_restart"];
                var needsRestartElement = mx.$("#serverNeedsRestart");
                needsRestartElement.style.display = daemonNeedsRestart ? "flex" : "";
            }

            if( data["job_status"] ) processRunningJobDetails(data["job_status"]);
        }

        function processData(last_data_modified, changed_data)
        {
            if( changed_data.hasOwnProperty("has_encrypted_vault") ) hasEncryptedVault = changed_data["has_encrypted_vault"];
            
            if( changed_data.hasOwnProperty("deployment_tags") ) deploymentTags = changed_data["deployment_tags"];
                 
            let updateBehaviorChanged = false;
            
            const [ lastUpdateDate, lastUpdateMsg ] = mx.UpdateServiceTemplates.getLastFullRefresh(last_data_modified);
            let lastUpdateDateElement = mx.$("#lastUpdateDateFormatted");
            if( lastUpdateMsg != lastUpdateDateElement.innerHTML ) 
            {
                lastUpdateDateElement.innerHTML = lastUpdateMsg;
                if( lastUpdateDate == null ) lastUpdateDateElement.classList.add("red");
                else lastUpdateDateElement.classList.remove("red");
                 
                updateBehaviorChanged = true
            }
            
            if( changed_data.hasOwnProperty("outdated_processes") || changed_data.hasOwnProperty("outdated_roles") )
            {
                mx.UpdateServiceTemplates.setSystemOutdatedDetails(last_data_modified, changed_data, "#systemStateHeader", "#systemStateDetails", "#roleStateHeader", "#roleStateDetails" );
            }
            
            if( changed_data.hasOwnProperty("is_reboot_needed") )
            {
                mx.UpdateServiceTemplates.setSystemStateDetails(last_data_modified, changed_data,"#systemRebootState")
            }

            if( changed_data.hasOwnProperty("system_updates") )
            {
                systemUpdatesCount = mx.UpdateServiceTemplates.setSystemUpdateDetails(last_data_modified, changed_data, lastUpdateDate, "#systemUpdateHeader", "#systemUpdateDetails");
                updateBehaviorChanged = true;
            }
            
            if( changed_data.hasOwnProperty("smartserver_changes") )
            {
                smartserverChangesCount = mx.UpdateServiceTemplates.setSmartserverChangeDetails(last_data_modified, changed_data, lastUpdateDate, "#smartserverChangeHeader", "#smartserverChangeDetails");
                updateBehaviorChanged = true;
            }
            
            if( changed_data.hasOwnProperty("smartserver_code") )
            {
                mx.UpdateServiceTemplates.setSmartserverChangeState(last_data_modified, changed_data, "#smartserverChangeState");
            }
            
            if( changed_data.hasOwnProperty("jobs") )
            {
                mx.UpdateServiceTemplates.setJobDetails(last_data_modified, changed_data, "#lastRunningJobsHeader", "#lastRunningJobsDetails");
            }

            if( updateBehaviorChanged )
            {
                mx.UpdateServiceTemplates.setWorkflow(systemUpdatesCount, smartserverChangesCount, lastUpdateDate, "#updateWorkflow");
            }
            
            let systemUpdatesHashChanged = false;
            let smartserverChangesHashChanged = false;
            let updateHashRefreshed = false;
            if( changed_data.hasOwnProperty("system_updates_hash") )
            {
                updateHashRefreshed = true;
                if( systemUpdatesHash != changed_data["system_updates_hash"] ) systemUpdatesHashChanged = true;
                systemUpdatesHash = changed_data["system_updates_hash"];
            }
            if( changed_data.hasOwnProperty("smartserver_changes_hash") )
            {
                updateHashRefreshed = true;
                if( smartserverChangesHash != changed_data["smartserver_changes_hash"] ) smartserverChangesHashChanged = true;
                smartserverChangesHash = changed_data["smartserver_changes_hash"];
            }
            
            //console.log(changed_data );
            //console.log(updateJobStarted + " " + updateHashRefreshed + " " + updateHashChanged );
            
            if( updateJobStarted && updateHashRefreshed )
            {
                updateJobStarted = false;
                if( systemUpdatesHashChanged || smartserverChangesHashChanged )
                {
                    let body = ""; 
                    if( systemUpdatesHashChanged && smartserverChangesHashChanged ) body += mx.I18N.get("There are new system and smartserver update available!");  
                    else if( systemUpdatesHashChanged ) body += mx.I18N.get("There are new system update available!");  
                    else if( smartserverChangesHashChanged ) body += mx.I18N.get("There are new smartserver update available!");  
            
                    let infoDialog = mx.Dialog.init({
                        id: "stoppedUpdate",
                        title: mx.I18N.get("Installation stopped!"),
                        body: body + "<span class='spacer'></span>" + mx.I18N.get("Please check whether you want to install these updates and restart the installation process if necessary."),
                        buttons: [
                            { "text": mx.I18N.get("Ok") },
                        ],
                        class: "confirmDialog",
                        destroy: true
                    });
                    infoDialog.open();
                    mx.Page.refreshUI(infoDialog.getRootElement());
                }
            }
            
            if( Object.keys(changed_data).length > 0 ) mx.Page.refreshUI();
        }
        
        function handleDaemonState(state)
        {
            window.clearTimeout(refreshDaemonStateTimer);

            job_is_running = state["job_is_running"];
            last_data_modified = state["last_data_modified"];
            
            if( job_is_running )
            {
                refreshDaemonStateTimer = window.setTimeout(function(){ refreshDaemonState(state["last_data_modified"], null) }, 1000);
            }
            else
            {
                refreshDaemonStateTimer = window.setTimeout(function(){ refreshDaemonState(state["last_data_modified"], null) }, 5000);
            }

            if( Object.keys(state["changed_data"]).length > 0 ) processData(state["last_data_modified"], state["changed_data"]);
        }
        
        function refreshDaemonState(last_data_modified,callback)
        {
            var xhr = new XMLHttpRequest();
            xhr.open("POST", daemonApiUrl + "state/" );
            xhr.setRequestHeader("Content-Type", "application/x-www-form-urlencoded");
            
            //application/x-www-form-urlencoded
            
            xhr.withCredentials = true;
            xhr.onreadystatechange = function() {
                if (this.readyState != 4) return;
                
                if( this.status == 200 ) 
                {
                    var response = JSON.parse(this.response);
                    if( response["status"] == "0" )
                    {
                        mx.Error.confirmSuccess();
                        mx.UpdateServiceHelper.confirmRestarting();
                        
                        handleDaemonState(response);
                        
                        if( callback ) callback();
                    }
                    else
                    {
                        mx.Error.handleServerError(response["message"])
                    }
                }
                else
                {
                    let timeout = 15000;
                    if( this.status == 0 || this.status == 503 ) 
                    {
                        mx.Error.handleError( mx.I18N.get( mx.UpdateServiceHelper.isRestarting() ? "Service is restarting" : "Service is currently not available")  );
                        timeout = mx.UpdateServiceHelper.isRestarting() ? 1000 : 15000;
                    }
                    else
                    {
                        if( this.status != 401 ) mx.Error.handleRequestError(this.status, this.statusText, this.response);
                    }
                    
                    refreshDaemonStateTimer = mx.Page.handleRequestError(this.status,daemonApiUrl,function(){ refreshDaemonState(last_data_modified, callback) }, timeout);
                }
            };
            
            xhr.send(mx.Core.encodeDict( { "type": "update", "last_data_modified": last_data_modified } ));
        }
        
        ret.setUpdateJobStarted = function( _updateJobStarted ){ updateJobStarted = _updateJobStarted; }
        
        ret.hasEncryptedVault = function(){ return hasEncryptedVault; }
        
        ret.getDeploymentTags = function(){ return deploymentTags; }

        ret.getLastDataModified = function(){ return last_data_modified; }
    
        ret.getSystemUpdatesCount = function(){ return systemUpdatesCount; }

        ret.getSmartserverChangesCount = function(){ return smartserverChangesCount; }

        ret.getLastDataModified = function(){ return last_data_modified; }

        ret.getUpdateHashes = function(){ return { "system_updates_hash": systemUpdatesHash, "smartserver_changes_hash": smartserverChangesHash }; }
        
        ret.handleDaemonState = function(state){ handleDaemonState(state); }
        
        ret.init = function()
        { 
            socket = mx.ServiceSocket.init('update_service');
            socket.on("connect", () => socket.emit("join", "updates") );
            socket.on("data", (data) => processDataNew( data ) );


            mx.I18N.process(document);
            mx.UpdateServiceActions.init(daemonApiUrl);
            
            mx.Selectbutton.init({
                values: [
                    { "text": mx.I18N.get("Only smartserver updates"), "onclick": function(){ mx.UpdateServiceActions.actionRefreshUpdateState(this,'deployment_update') } },
                    { "text": mx.I18N.get("Only system updates"), "onclick": function(){ mx.UpdateServiceActions.actionRefreshUpdateState(this,'system_update') } },
                    { "text": mx.I18N.get("Only outdated processes"), "onclick": function(){ mx.UpdateServiceActions.actionRefreshUpdateState(this,'process_update') } }
                ],
                selectors: {
                    button: "#searchUpdates"
                }
            });
          
            refreshDaemonState(null, function(){
                window.setTimeout(function(){
                    var initialLists = ["systemProcesses","smartserverRoles"];
                    initialLists.forEach(function(id){
                        var element = mx.$("#" + id);
                        if( element ) element.click();
                    });
                },100);
            });

            mx.Page.refreshUI();            
        }
        return ret;
    })( mx.UNCore || {} );
    
    mx.OnDocReady.push( mx.UNCore.init );
</script>
</head>
<body class="system">
<script>mx.OnScriptReady.push( function(){ mx.Page.initFrame("spacer", mx.I18N.get("Update")); } );</script>
<div class="widget summery">
    <div class="action" id="updateWorkflow"></div>
    <div class="action"><div class="info" id="lastUpdateDateFormatted"></div><div class="buttons"><div class="form button exclusive" id="searchUpdates" onclick="mx.UpdateServiceActions.actionRefreshUpdateState(this)" data-i18n="Check for updates"></div></div></div>
</div>
<div class="widget">
    <div class="header"><div data-i18n="Status"></div></div>

    <div class="action" id="serverNeedsRestart"><div class="info"><span class="icon-attention red"></span> <span data-i18n="Daemon was updated and needs to restart"></span></div><div class="buttons"><div class="form button restart red exclusive" onclick="mx.UpdateServiceActions.actionRestartDaemon(this)" data-i18n="Restart daemon"></div></div></div>
    
    <div class="action"><div class="info" id="currentRunningState"></div><div class="buttons" id="currentRunningActions"><div class="form button kill red" onclick="mx.UpdateServiceActions.actionKillProcess(this)" data-i18n="Stop"></div></div></div>
    <div class="action" id="lastRunningJobsHeader"></div>
    <div id="lastRunningJobsDetails"></div>

    <div class="action" id="systemRebootState"></div>
    
    <div class="action" id="systemStateHeader"></div>
    <div id="systemStateDetails"></div>
    
    <div class="action" id="roleStateHeader"></div>
    <div id="roleStateDetails"></div>
</div>
<div class="widget">
    <div class="header"><div data-i18n="Details"></div></div>
   
    <div class="action" id="systemUpdateHeader"></div>
    <div id="systemUpdateDetails"></div>

    <div class="action" id="smartserverChangeHeader"></div>
    <div id="smartserverChangeDetails"></div>
    <div class="action" id="smartserverChangeState"></div>
</div>
</body>
</html>
