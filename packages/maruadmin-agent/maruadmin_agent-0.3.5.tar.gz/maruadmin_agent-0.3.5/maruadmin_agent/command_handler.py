"""
Command handler for processing agent commands
"""
import json
import logging
import subprocess
from datetime import datetime
from typing import Any, Dict, Optional

from .utils import execute_command, get_docker_info, get_system_info
from .certificate_manager import CertificateManager
from .haproxy_manager import HAProxyManager


class CommandHandler:
    """Handler for agent commands"""

    def __init__(self, config: Any, logger: logging.Logger):
        """
        Initialize command handler

        Args:
            config: Agent configuration
            logger: Logger instance
        """
        self.config = config
        self.logger = logger

        # Initialize managers
        self.haproxy_manager = HAProxyManager()
        self.certificate_manager = CertificateManager(haproxy_manager=self.haproxy_manager)

        # Register command handlers
        self.handlers = {
            'ping': self.handle_ping,
            'info': self.handle_info,
            'exec': self.handle_exec,
            'docker': self.handle_docker,
            'service': self.handle_service,
            'file': self.handle_file,
            'update': self.handle_update,
            'restart': self.handle_restart,
            'ssh_key': self.handle_ssh_key,
            'uninstall': self.handle_uninstall,
            'certificate': self.handle_certificate,
            'haproxy': self.handle_haproxy,
        }

    def handle_command(self, command: Dict[str, Any]) -> Dict[str, Any]:
        """
        Handle incoming command

        Args:
            command: Command dictionary with 'type' and optional 'params'

        Returns:
            Response dictionary
        """
        command_type = command.get('type')
        params = command.get('params', {})

        self.logger.info(f"Processing command: {command_type}")

        # Get handler for command type
        handler = self.handlers.get(command_type)

        if not handler:
            return {
                'success': False,
                'error': f'Unknown command type: {command_type}',
                'timestamp': datetime.utcnow().isoformat()
            }

        try:
            # Execute handler
            result = handler(params)
            result['timestamp'] = datetime.utcnow().isoformat()
            return result

        except Exception as e:
            self.logger.error(f"Error executing command {command_type}: {e}")
            return {
                'success': False,
                'error': str(e),
                'timestamp': datetime.utcnow().isoformat()
            }

    def handle_ping(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle ping command"""
        return {
            'success': True,
            'message': 'pong',
            'agent_id': self.config.agent_id,
            'agent_name': self.config.agent_name
        }

    def handle_info(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle info command"""
        info_type = params.get('type', 'all')

        if info_type == 'system' or info_type == 'all':
            system_info = get_system_info()
        else:
            system_info = None

        if info_type == 'docker' or info_type == 'all':
            docker_info = get_docker_info()
        else:
            docker_info = None

        return {
            'success': True,
            'system': system_info,
            'docker': docker_info,
            'agent': {
                'id': self.config.agent_id,
                'name': self.config.agent_name,
                'version': '0.1.0',
                'config': {
                    'heartbeat_interval': self.config.heartbeat_interval,
                    'monitor_interval': self.config.monitor_interval,
                    'ssh_port': self.config.ssh_port,
                }
            }
        }

    def handle_exec(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle exec command"""
        command = params.get('command')
        timeout = params.get('timeout', 30)

        if not command:
            return {
                'success': False,
                'error': 'No command specified'
            }

        # Security check - allow only specific commands or patterns
        # In production, implement proper command validation
        allowed_prefixes = [
            'docker', 'systemctl', 'service', 'ls', 'cat', 'grep',
            'ps', 'top', 'df', 'du', 'free', 'netstat', 'ss'
        ]

        command_parts = command.split()
        if not any(command_parts[0].startswith(prefix) for prefix in allowed_prefixes):
            return {
                'success': False,
                'error': f'Command not allowed: {command_parts[0]}'
            }

        # Execute command
        result = execute_command(command, timeout)
        return result

    def handle_docker(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle Docker commands"""
        action = params.get('action')

        if action == 'ps':
            # List containers
            result = execute_command('docker ps -a --format json', timeout=10)

            if result['success']:
                containers = []
                for line in result['stdout'].strip().split('\n'):
                    if line:
                        containers.append(json.loads(line))

                return {
                    'success': True,
                    'containers': containers
                }

        elif action == 'images':
            # List images
            result = execute_command('docker images --format json', timeout=10)

            if result['success']:
                images = []
                for line in result['stdout'].strip().split('\n'):
                    if line:
                        images.append(json.loads(line))

                return {
                    'success': True,
                    'images': images
                }

        elif action == 'start':
            container_id = params.get('container_id')
            if not container_id:
                return {'success': False, 'error': 'No container ID specified'}

            result = execute_command(f'docker start {container_id}', timeout=10)
            return result

        elif action == 'stop':
            container_id = params.get('container_id')
            if not container_id:
                return {'success': False, 'error': 'No container ID specified'}

            result = execute_command(f'docker stop {container_id}', timeout=10)
            return result

        elif action == 'restart':
            container_id = params.get('container_id')
            if not container_id:
                return {'success': False, 'error': 'No container ID specified'}

            result = execute_command(f'docker restart {container_id}', timeout=10)
            return result

        elif action == 'logs':
            container_id = params.get('container_id')
            lines = params.get('lines', 100)

            if not container_id:
                return {'success': False, 'error': 'No container ID specified'}

            result = execute_command(f'docker logs --tail {lines} {container_id}', timeout=10)
            return result

        else:
            return {
                'success': False,
                'error': f'Unknown Docker action: {action}'
            }

    def handle_service(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle service management commands"""
        action = params.get('action')
        service = params.get('service')

        if not service:
            return {
                'success': False,
                'error': 'No service specified'
            }

        # Security check - allow only specific services
        allowed_services = [
            'nginx', 'apache2', 'httpd', 'mysql', 'postgresql',
            'redis', 'docker', 'ssh', 'maruadmin-agent'
        ]

        if service not in allowed_services:
            return {
                'success': False,
                'error': f'Service not allowed: {service}'
            }

        if action == 'status':
            result = execute_command(f'systemctl status {service}', timeout=5)

        elif action == 'start':
            result = execute_command(f'systemctl start {service}', timeout=10)

        elif action == 'stop':
            result = execute_command(f'systemctl stop {service}', timeout=10)

        elif action == 'restart':
            result = execute_command(f'systemctl restart {service}', timeout=10)

        elif action == 'enable':
            result = execute_command(f'systemctl enable {service}', timeout=5)

        elif action == 'disable':
            result = execute_command(f'systemctl disable {service}', timeout=5)

        else:
            return {
                'success': False,
                'error': f'Unknown service action: {action}'
            }

        return result

    def handle_file(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle file operations"""
        action = params.get('action')
        path = params.get('path')

        if not path:
            return {
                'success': False,
                'error': 'No path specified'
            }

        # Security check - allow only specific paths
        allowed_paths = [
            '/var/log/',
            '/etc/nginx/',
            '/etc/apache2/',
            '/etc/maruadmin/'
        ]

        if not any(path.startswith(prefix) for prefix in allowed_paths):
            return {
                'success': False,
                'error': f'Path not allowed: {path}'
            }

        if action == 'read':
            try:
                with open(path, 'r') as f:
                    content = f.read()

                return {
                    'success': True,
                    'content': content,
                    'path': path
                }

            except Exception as e:
                return {
                    'success': False,
                    'error': str(e)
                }

        elif action == 'write':
            content = params.get('content')
            if content is None:
                return {
                    'success': False,
                    'error': 'No content specified'
                }

            try:
                with open(path, 'w') as f:
                    f.write(content)

                return {
                    'success': True,
                    'path': path
                }

            except Exception as e:
                return {
                    'success': False,
                    'error': str(e)
                }

        else:
            return {
                'success': False,
                'error': f'Unknown file action: {action}'
            }

    def handle_update(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle agent update command"""
        self.logger.info("=== Starting agent upgrade process ===")

        # Upgrade agent package and restart service in background
        import threading

        def upgrade_agent():
            import time
            time.sleep(2)  # Wait for response to be sent

            try:
                self.logger.info("Executing pip upgrade command...")

                # Get current version before upgrade
                version_cmd = '/opt/maruadmin/venv/bin/pip show maruadmin-agent'
                version_result = execute_command(version_cmd, timeout=10)
                old_version = "unknown"
                if version_result['success']:
                    for line in version_result['stdout'].split('\n'):
                        if line.startswith('Version:'):
                            old_version = line.split(':')[1].strip()
                            break

                self.logger.info(f"Current version: {old_version}")

                # Upgrade command - use venv pip with sudo
                upgrade_cmd = 'sudo /opt/maruadmin/venv/bin/pip install --upgrade maruadmin-agent'
                self.logger.info(f"Running: {upgrade_cmd}")
                result = execute_command(upgrade_cmd, timeout=120)

                if result['success']:
                    self.logger.info("Pip upgrade command completed successfully")
                    self.logger.info(f"Upgrade output: {result['stdout']}")

                    # Get new version after upgrade
                    version_result = execute_command(version_cmd, timeout=10)
                    new_version = "unknown"
                    if version_result['success']:
                        for line in version_result['stdout'].split('\n'):
                            if line.startswith('Version:'):
                                new_version = line.split(':')[1].strip()
                                break

                    self.logger.info(f"Upgraded from {old_version} to {new_version}")

                    # Restart agent service
                    self.logger.info("Restarting agent service...")
                    restart_result = execute_command('sudo systemctl restart maruadmin-agent', timeout=10)

                    if restart_result['success']:
                        self.logger.info("Agent service restart initiated successfully")
                    else:
                        self.logger.error(f"Failed to restart agent service: {restart_result.get('error')}")
                else:
                    self.logger.error(f"Agent upgrade failed: {result.get('error')}")
                    self.logger.error(f"Stdout: {result.get('stdout', '')}")
                    self.logger.error(f"Stderr: {result.get('stderr', '')}")

            except Exception as e:
                self.logger.error(f"Exception during agent upgrade: {str(e)}", exc_info=True)

        thread = threading.Thread(target=upgrade_agent)
        thread.daemon = True
        thread.start()

        self.logger.info("Agent upgrade thread started")
        return {
            'success': True,
            'message': 'Agent upgrade initiated. Check logs for progress.'
        }

    def handle_restart(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle agent restart command"""
        self.logger.info("Restarting agent...")

        # Schedule restart after response
        import threading

        def restart_agent():
            import time
            time.sleep(2)
            execute_command('systemctl restart maruadmin-agent', timeout=5)

        thread = threading.Thread(target=restart_agent)
        thread.daemon = True
        thread.start()

        return {
            'success': True,
            'message': 'Agent restart scheduled'
        }

    def handle_ssh_key(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle SSH key management commands"""
        action = params.get('action')
        public_key = params.get('public_key')

        if not action:
            return {
                'success': False,
                'error': 'No action specified'
            }

        # Get user from config or use default
        user = params.get('user') or self.config.ssh_user or 'root'

        # Determine authorized_keys path
        if user == 'root':
            authorized_keys_path = '/root/.ssh/authorized_keys'
        else:
            authorized_keys_path = f'/home/{user}/.ssh/authorized_keys'

        if action == 'install':
            if not public_key:
                return {
                    'success': False,
                    'error': 'No public key specified'
                }

            try:
                # Ensure .ssh directory exists
                ssh_dir = authorized_keys_path.rsplit('/', 1)[0]
                execute_command(f'mkdir -p {ssh_dir}', timeout=5)
                execute_command(f'chmod 700 {ssh_dir}', timeout=5)

                # Check if key already exists
                check_result = execute_command(
                    f'grep -F "{public_key}" {authorized_keys_path}',
                    timeout=5
                )

                if check_result['exit_code'] == 0:
                    self.logger.info("SSH key already exists in authorized_keys")
                    return {
                        'success': True,
                        'message': 'SSH key already exists',
                        'path': authorized_keys_path
                    }

                # Append public key to authorized_keys
                result = execute_command(
                    f'echo "{public_key}" >> {authorized_keys_path}',
                    timeout=5
                )

                if result['success']:
                    # Set correct permissions
                    execute_command(f'chmod 600 {authorized_keys_path}', timeout=5)
                    execute_command(f'chown {user}:{user} {authorized_keys_path}', timeout=5)

                    self.logger.info(f"SSH key installed successfully to {authorized_keys_path}")
                    return {
                        'success': True,
                        'message': 'SSH key installed successfully',
                        'path': authorized_keys_path
                    }
                else:
                    return {
                        'success': False,
                        'error': f"Failed to install SSH key: {result.get('stderr', 'Unknown error')}"
                    }

            except Exception as e:
                self.logger.error(f"Error installing SSH key: {e}")
                return {
                    'success': False,
                    'error': str(e)
                }

        elif action == 'remove':
            if not public_key:
                return {
                    'success': False,
                    'error': 'No public key specified'
                }

            try:
                # Check if authorized_keys exists
                check_file = execute_command(f'test -f {authorized_keys_path}', timeout=5)
                if check_file['exit_code'] != 0:
                    return {
                        'success': True,
                        'message': 'authorized_keys file does not exist'
                    }

                # Create a backup
                execute_command(f'cp {authorized_keys_path} {authorized_keys_path}.bak', timeout=5)

                # Remove the key using sed (escape special characters)
                escaped_key = public_key.replace('/', '\\/')
                result = execute_command(
                    f'sed -i "\\|{escaped_key}|d" {authorized_keys_path}',
                    timeout=5
                )

                if result['success']:
                    self.logger.info(f"SSH key removed successfully from {authorized_keys_path}")
                    return {
                        'success': True,
                        'message': 'SSH key removed successfully',
                        'path': authorized_keys_path
                    }
                else:
                    # Restore backup on failure
                    execute_command(f'mv {authorized_keys_path}.bak {authorized_keys_path}', timeout=5)
                    return {
                        'success': False,
                        'error': f"Failed to remove SSH key: {result.get('stderr', 'Unknown error')}"
                    }

            except Exception as e:
                self.logger.error(f"Error removing SSH key: {e}")
                # Try to restore backup
                execute_command(f'mv {authorized_keys_path}.bak {authorized_keys_path}', timeout=5)
                return {
                    'success': False,
                    'error': str(e)
                }

        elif action == 'list':
            try:
                # Read authorized_keys file
                result = execute_command(f'cat {authorized_keys_path}', timeout=5)

                if result['success']:
                    keys = [line.strip() for line in result['stdout'].split('\n') if line.strip()]
                    return {
                        'success': True,
                        'keys': keys,
                        'count': len(keys),
                        'path': authorized_keys_path
                    }
                else:
                    return {
                        'success': False,
                        'error': f"Failed to read authorized_keys: {result.get('stderr', 'File not found')}"
                    }

            except Exception as e:
                self.logger.error(f"Error listing SSH keys: {e}")
                return {
                    'success': False,
                    'error': str(e)
                }

        else:
            return {
                'success': False,
                'error': f'Unknown SSH key action: {action}'
            }

    def handle_uninstall(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle agent uninstall command"""
        self.logger.info("Uninstalling agent...")

        # Schedule uninstall after response
        import threading

        def uninstall_agent():
            import time
            time.sleep(2)

            # Download and execute uninstall script
            uninstall_url = params.get('uninstall_url', 'https://gist.githubusercontent.com/dirmich/f335e8ce73ea2d95591b9764ce0ff01f/raw/uninstall.sh')
            execute_command(f'curl -sSL {uninstall_url} | sudo bash -s -- -y', timeout=30)

        thread = threading.Thread(target=uninstall_agent)
        thread.daemon = True
        thread.start()

        return {
            'success': True,
            'message': 'Agent uninstall scheduled'
        }

    def handle_certificate(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle certificate management commands"""
        action = params.get('action')

        if not action:
            return {
                'success': False,
                'error': 'No action specified'
            }

        try:
            if action == 'issue':
                # Issue new certificate
                domain = params.get('domain')
                email = params.get('email')
                validation_method = params.get('validation_method', 'http')
                wildcard = params.get('wildcard', False)
                dns_provider = params.get('dns_provider')
                dns_provider_config = params.get('dns_provider_config')

                if not domain or not email:
                    return {
                        'success': False,
                        'error': 'Domain and email are required'
                    }

                # If DNS provider config is provided, create a new certificate manager with it
                if dns_provider_config:
                    cert_manager = CertificateManager(
                        haproxy_manager=self.haproxy_manager,
                        dns_provider_config=dns_provider_config
                    )
                else:
                    cert_manager = self.certificate_manager

                result = cert_manager.issue_certificate(
                    domain=domain,
                    email=email,
                    validation_method=validation_method,
                    wildcard=wildcard,
                    dns_provider=dns_provider
                )

                return {
                    'success': result['status'] == 'success',
                    'data': result
                }

            elif action == 'renew':
                # Renew certificate(s)
                domain = params.get('domain')
                result = self.certificate_manager.renew_certificate(domain=domain)

                return {
                    'success': result['status'] == 'success',
                    'data': result
                }

            elif action == 'list':
                # List all certificates
                result = self.certificate_manager.list_certificates()

                return {
                    'success': result['status'] == 'success',
                    'data': result
                }

            elif action == 'revoke':
                # Revoke certificate
                domain = params.get('domain')
                if not domain:
                    return {
                        'success': False,
                        'error': 'Domain is required'
                    }

                result = self.certificate_manager.revoke_certificate(domain=domain)

                return {
                    'success': result['status'] == 'success',
                    'data': result
                }

            elif action == 'delete':
                # Delete certificate
                domain = params.get('domain')
                if not domain:
                    return {
                        'success': False,
                        'error': 'Domain is required'
                    }

                result = self.certificate_manager.delete_certificate(domain=domain)

                return {
                    'success': result['status'] == 'success',
                    'data': result
                }

            elif action == 'install_certbot':
                # Install certbot
                result = self.certificate_manager.install_certbot()

                return {
                    'success': result['status'] == 'success',
                    'data': result
                }

            else:
                return {
                    'success': False,
                    'error': f'Unknown certificate action: {action}'
                }

        except Exception as e:
            self.logger.error(f"Error in certificate handler: {e}")
            return {
                'success': False,
                'error': str(e)
            }

    def handle_haproxy(self, params: Dict[str, Any]) -> Dict[str, Any]:
        """Handle HAProxy management commands"""
        action = params.get('action')

        if not action:
            return {
                'success': False,
                'error': 'No action specified'
            }

        try:
            if action == 'install':
                # Install HAProxy
                result = self.haproxy_manager.install_haproxy()
                return {
                    'success': result['status'] == 'success',
                    'data': result
                }

            elif action == 'update_config':
                # Update HAProxy configuration
                config = params.get('config')
                domain_map = params.get('domain_map', '')

                if not config:
                    return {
                        'success': False,
                        'error': 'Configuration is required'
                    }

                result = self.haproxy_manager.update_configuration(config, domain_map)
                return {
                    'success': result['status'] == 'success',
                    'data': result
                }

            elif action == 'reload':
                # Reload HAProxy
                result = self.haproxy_manager.reload_service()
                return {
                    'success': result['status'] == 'success',
                    'data': result
                }

            elif action == 'restart':
                # Restart HAProxy
                result = self.haproxy_manager.restart_service()
                return {
                    'success': result['status'] == 'success',
                    'data': result
                }

            elif action == 'status':
                # Get HAProxy status
                result = self.haproxy_manager.get_status()
                return {
                    'success': result['status'] == 'success',
                    'data': result
                }

            elif action == 'stats':
                # Get HAProxy statistics
                result = self.haproxy_manager.get_statistics()
                return {
                    'success': result['status'] == 'success',
                    'data': result
                }

            elif action == 'sync_certificates':
                # Sync Let's Encrypt certificates
                result = self.haproxy_manager.sync_letsencrypt_certificates()
                return {
                    'success': result['status'] == 'success',
                    'data': result
                }

            else:
                return {
                    'success': False,
                    'error': f'Unknown HAProxy action: {action}'
                }

        except Exception as e:
            self.logger.error(f"Error in HAProxy handler: {e}")
            return {
                'success': False,
                'error': str(e)
            }