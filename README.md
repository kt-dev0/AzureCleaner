# AzureCleaner

**AzureCleaner** is a command-line tool that helps you clean up and optimize your Azure subscriptions by identifying unused or underutilized resources and reporting potential cost savings. It's designed for cloud engineers, DevOps teams, and FinOps professionals looking to reduce Azure spend and maintain a tidy environment.

## Features
- Scans one or all Azure subscriptions
- Identifies unused:
  - Public IP addresses
  - Network interfaces (NICs)
  - Network security groups (NSGs)
  - Managed disks
  - Empty resource groups
  - Stopped virtual machines
  - Unused load balancers
  - Stopped web apps
  - Empty DNS zones
  - Unused route tables
  - Application gateways with no config
  - Empty recovery services vaults
  - Inactive container registries
- Provides Azure CLI commands to delete each item
- Calculates live estimated subscription cost via Azure Consumption API

## Installation
1. Clone the repository:
   ```bash
   git clone https://github.com/yourusername/azurecleaner.git
   cd azurecleaner
   ```
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```

> Note: You must have Azure CLI installed and authenticated with `az login`.

## Usage
Run the tool using Python:
```bash
python azurecleaner.py
```

You will be prompted to select a specific Azure subscription or scan all available subscriptions.

### Example Output
```
Starting AzureCleaner Scan...
Available Subscriptions:
[1] Dev Subscription (xxxx-xxxx-xxxx-xxxx)
[2] Prod Subscription (yyyy-yyyy-yyyy-yyyy)
[0] All Subscriptions
Select a subscription by number (or 0 for all): 1

Scanning subscription: Dev Subscription (xxxx-xxxx-xxxx-xxxx)
Current Subscription Cost (Live): $243.81

Public Ips (2)
• unused-ip-01 | RG: network-resources
  az CLI: az network public-ip delete -g network-resources -n unused-ip-01
```

## Requirements
- Python 3.7+
- Azure CLI
- Logged in with `az login`


## License
MIT License

