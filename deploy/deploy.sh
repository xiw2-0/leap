export WINEPREFIX=/opt/leap/wine

sudo -u leap mkdir -p /opt/leap/release/$(date +%Y%m%d)

sudo -u leap mv /home/x/*.whl /opt/leap/release/$(date +%Y%m%d)
sudo -u leap mv /home/x/.env /opt/leap/release/$(date +%Y%m%d)

sudo -u leap ln -sf /opt/leap/release/$(date +%Y%m%d) /opt/leap/current

sudo -E -u leap wine python -m pip uninstall -y leap
sudo -E -u leap wine python -m pip install -i https://pypi.tuna.tsinghua.edu.cn/simple Z:/opt/leap/current/leap-0.1.0-py3-none-any.whl