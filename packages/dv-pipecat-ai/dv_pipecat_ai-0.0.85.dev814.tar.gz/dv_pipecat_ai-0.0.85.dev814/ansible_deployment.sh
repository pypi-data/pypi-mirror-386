# ansible_deployment.sh
#!/bin/bash

# Run ansible playbook
ansible-playbook -i inventory.ini deploy_playbook.yml

# Created/Modified files during execution:
echo "ansible_deployment.sh"