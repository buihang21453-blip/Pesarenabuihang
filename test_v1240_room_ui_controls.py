from pathlib import Path
R=Path(__file__).resolve().parent

def read(p): return (R/p).read_text(encoding='utf-8')

def test_version_and_fields():
    assert 'APP_VERSION = "V1.2.40"' in read('app.py')
    service=read('modules/admin_room_ui/service.py')
    for key in ['header_height','share_button_width','share_button_height','share_button_font_size','active_mode_logo_size','center_button_font_size','right_rail_font_size','mode_cluster_height']:
        assert f'"{key}"' in service

def test_share_icon_removed_and_vars_connected():
    tpl=read('templates/room_detail.html')
    assert 'room-share-icon' not in tpl
    for var in ['--rui-header-height','--rui-share-width','--rui-active-size','--rui-center-button-font-size','--rui-right-font-size','--rui-mode-cluster-height']:
        assert var in tpl

def test_mode_logo_normalization_and_status_reserved():
    css=read('static/css/room_v2.css')
    assert '.room-v2-mode-card.mode-7 img{transform:scale(.78)!important}' in css
    assert 'grid-template-rows:minmax(0,1fr) 22px 22px!important' in css
    assert 'height:22px!important' in css

def test_admin_controls_present():
    tpl=read('templates/admin/tabs/room-ui.html')
    for label in ['Chiều cao thanh PHÒNG ĐẤU','Nút Chia sẻ - rộng','Logo chế độ đang chọn','Chiều cao 3 nút','Size font cột phải','Chiều cao cả cụm 7 chế độ']:
        assert label in tpl
