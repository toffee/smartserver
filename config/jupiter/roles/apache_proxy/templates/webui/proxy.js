var html = '<div class="service imageWatcher">';
//html += '<div style="cursor:pointer" onClick="mx.Actions.openEntryById(event,\'automation\',\'cameras\',\'camera_streedside\')"><img src="/main/img/loading.png" data-name="{i18n_Street}" data-src="/cameraStrasseImage" data-interval="3000"></div>';
//html += '<div><img src="/main/img/loading.png" data-name="{i18n_Automower}" data-src="/cameraAutomowerImage" data-interval="3000"></div>';
html += '</div>';

var cameraSubGroup = mx.Menu.getMainGroup('automation').addSubGroup('cameras', 900, '{i18n_Cameras}', 'proxy_camera.svg');
//cameraSubGroup.addHtml('cameras', html, function(){ mx.ImageWatcher.init('.service.imageWatcher > div'); }, 'user', 100 );
cameraSubGroup.addUrl('camera_01','https://{{camera_01_ip}}', 'user', 901, '{i18n_Camera_01}', '{i18n_Camera_01}', 'proxy_camera.svg', true);
cameraSubGroup.addUrl('camera_02','https://{{camera_02_ip}}', 'user', 902, '{i18n_Camera_02}', '{i18n_Camera_02}', 'proxy_camera.svg', true);
cameraSubGroup.addUrl('camera_03','https://{{camera_03_ip}}', 'user', 903, '{i18n_Camera_03}', '{i18n_Camera_03}', 'proxy_camera.svg', true);
cameraSubGroup.addUrl('camera_04','https://{{camera_04_ip}}', 'user', 904, '{i18n_Camera_04}', '{i18n_Camera_04}', 'proxy_camera.svg', true);
cameraSubGroup.addUrl('camera_09','https://{{camera_09_ip}}', 'user', 909, '{i18n_Camera_09}', '{i18n_Camera_09}', 'proxy_camera.svg', true);

var subGroup = mx.Menu.getMainGroup('admin').getSubGroup('devices');
subGroup.addUrl('router', 'http://{{router_ip}}', 'admin', 250, '{i18n_Router}', '{i18n_Router (Extern)}', 'router.svg', true);
subGroup.addUrl('switch', 'https://{{switch_ip}}', 'admin', 251, '{i18n_Switch}', '{i18n_Switch}', 'switch.svg', true);
