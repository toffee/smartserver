var html = '<div class="service imageWatcher">';
//html += '<div style="cursor:pointer" onClick="mx.Actions.openEntryById(event,\'automation\',\'cameras\',\'camera_streedside\')"><img src="/main/img/loading.png" data-name="{i18n_Street}" data-src="/cameraStrasseImage" data-interval="3000"></div>';
//html += '<div><img src="/main/img/loading.png" data-name="{i18n_Automower}" data-src="/cameraAutomowerImage" data-interval="3000"></div>';
html += '</div>';
html += '<div class="service imageWatcher">';
html += '<div style="cursor:pointer" onClick="mx.Actions.openEntryById(event,\'automation\',\'cameras\',\'camera_01\')"><img src="/main/img/loading.png" data-name="{i18n_Camera_01}" data-src="/camera01Image" data-interval="3000"></div>';
//html += '<div><img src="/main/img/loading.png" data-name="{i18n_Camera_02}" data-src="/camera02Image" data-interval="3000"></div>';
html += '</div>';
html += '<div class="service imageWatcher">';
html += '<div><img src="/main/img/loading.png" data-name="{i18n_Camera_03}" data-src="/camera03Image" data-interval="3000"></div>';
html += '<div><img src="/main/img/loading.png" data-name="{i18n_Camera_04}" data-src="/camera04Image" data-interval="3000"></div>';
html += '</div>';
html += '<div class="service imageWatcher">';
html += '<div><img src="/main/img/loading.png" data-name="{i18n_Camera_07}" data-src="/camera07Image" data-interval="3000"></div>';
html += '<div><img src="/main/img/loading.png" data-name="{i18n_Camera_09}" data-src="/camera09Image" data-interval="3000"></div>';
html += '</div>';

var cameraSubGroup = mx.Menu.getMainGroup('automation').addSubGroup('cameras', 900, '{i18n_Cameras}', 'proxy_camera.svg');
//cameraSubGroup.addHtml('cameras', html, function(){ mx.ImageWatcher.init('.service.imageWatcher > div'); }, 'user', 100 );
//cameraSubGroup.addUrl('camera_01','/gallery/?sub=camera');

