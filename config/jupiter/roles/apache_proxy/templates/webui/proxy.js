var html = '<div class="service imageWatcher">';
//html += '<div style="cursor:pointer" onClick="mx.Actions.openEntryById(event,\'automation\',\'cameras\',\'camera_streedside\')"><img src="/main/img/loading.png" data-name="{i18n_Street}" data-src="/cameraStrasseImage" data-interval="3000"></div>';
//html += '<div><img src="/main/img/loading.png" data-name="{i18n_Automower}" data-src="/cameraAutomowerImage" data-interval="3000"></div>';
html += '</div>';

var cameraSubGroup = mx.Menu.getMainGroup('automation').addSubGroup('cameras', 900, '{i18n_Cameras}', 'proxy_camera.svg');
//cameraSubGroup.addHtml('cameras', html, function(){ mx.ImageWatcher.init('.service.imageWatcher > div'); }, 'user', 100 );
//cameraSubGroup.addUrl('camera_01','/gallery/?sub=camera');

var subGroup = mx.Menu.getMainGroup('admin').getSubGroup('devices');
subGroup.addUrl('router', 'http://{{router_ip}}', 'admin', 200, '{i18n_Router}', '{i18n_Router (Extern)}', true, 'huawei.svg');
subGroup.addUrl('switch', 'https://{{switch_ip}}', 'admin', 300, '{i18n_Switch}', '{i18n_Switch}', true);
