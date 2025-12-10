#!/bin/bash
# Fix Samba share path to point to correct directory

echo "Fixing Samba configuration path..."
sudo sed -i 's|path = /home/jason_nguyen/visual-aoi-server/shared|path = /home/jason_nguyen/feyes/server/shared|' /etc/samba/smb.conf

echo "Restarting Samba service..."
sudo systemctl restart smbd

echo ""
echo "Updated Samba configuration:"
grep -A 10 '[visual-aoi-shared]' /etc/samba/smb.conf

echo ""
echo "✓ Samba share now points to: /home/jason_nguyen/feyes/server/shared"
