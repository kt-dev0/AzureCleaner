# AzureCleaner CLI-based UI

# MIT License

# Copyright (c) 2025 Kareem T

# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:

# Azure CLI-based authentication using SDK
from azure.identity import AzureCliCredential
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.compute import ComputeManagementClient
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.web import WebSiteManagementClient
from azure.mgmt.recoveryservicesbackup import RecoveryServicesBackupClient
from azure.mgmt.containerregistry import ContainerRegistryManagementClient
from azure.mgmt.dns import DnsManagementClient
from azure.mgmt.resource import SubscriptionClient
from azure.mgmt.consumption import ConsumptionManagementClient
import os

class CleanAzureScanner:
    def __init__(self, subscription_id=None):
        self.credential = AzureCliCredential()

        if not subscription_id:
            subscription_id = self.get_current_subscription_id()

        self.subscription_id = subscription_id

        self.resource_client = ResourceManagementClient(self.credential, self.subscription_id)
        self.network_client = NetworkManagementClient(self.credential, self.subscription_id)
        self.compute_client = ComputeManagementClient(self.credential, self.subscription_id)
        self.web_client = WebSiteManagementClient(self.credential, self.subscription_id)
        self.backup_client = RecoveryServicesBackupClient(self.credential, self.subscription_id)
        self.acr_client = ContainerRegistryManagementClient(self.credential, self.subscription_id)
        self.dns_client = DnsManagementClient(self.credential, self.subscription_id)
        self.consumption_client = ConsumptionManagementClient(self.credential, self.subscription_id)

    def get_current_subscription_id(self):
        sub_client = SubscriptionClient(self.credential)
        subs = list(sub_client.subscriptions.list())
        if not subs:
            raise RuntimeError("No active Azure subscriptions found. Please run 'az login'.")
        print("📋 Available Subscriptions:")
        for idx, sub in enumerate(subs):
            print(f"[{idx + 1}] {sub.display_name} ({sub.subscription_id})")
        selection = input("Select a subscription by number: ")
        try:
            selected_index = int(selection.strip()) - 1
            return subs[selected_index].subscription_id
        except (ValueError, IndexError):
            raise RuntimeError("Invalid subscription selection.")

    def get_live_cost_summary(self):
        try:
            usage = self.consumption_client.usage_details.list(scope=f"/subscriptions/{self.subscription_id}")
            total = 0.0
            for item in usage:
                if item.pretax_cost:
                    total += float(item.pretax_cost)
            return round(total, 2)
        except Exception as e:
            print(f"⚠️ Could not fetch live cost: {e}")
            return None

    def get_unused_public_ips(self):
        return [
            {
                "name": ip.name,
                "resource_group": ip.id.split("/")[4],
                "location": ip.location,
                "az_cli": f"az network public-ip delete -g {ip.id.split('/')[4]} -n {ip.name}"
            }
            for ip in self.network_client.public_ip_addresses.list_all()
            if not ip.ip_configuration
        ]

    def get_unattached_nics(self):
        return [
            {
                "name": nic.name,
                "resource_group": nic.id.split("/")[4],
                "location": nic.location,
                "az_cli": f"az network nic delete -g {nic.id.split('/')[4]} -n {nic.name}"
            }
            for nic in self.network_client.network_interfaces.list_all()
            if not nic.virtual_machine
        ]

    def get_orphaned_nsgs(self):
        return [
            {
                "name": nsg.name,
                "resource_group": nsg.id.split("/")[4],
                "location": nsg.location,
                "az_cli": f"az network nsg delete -g {nsg.id.split('/')[4]} -n {nsg.name}"
            }
            for nsg in self.network_client.network_security_groups.list_all()
            if not nsg.network_interfaces and not nsg.subnets
        ]

    def get_unattached_disks(self):
        return [
            {
                "name": disk.name,
                "resource_group": disk.id.split("/")[4],
                "location": disk.location,
                "az_cli": f"az disk delete -g {disk.id.split('/')[4]} -n {disk.name} --yes"
            }
            for disk in self.compute_client.disks.list()
            if disk.managed_by is None
        ]

    def get_empty_resource_groups(self):
        return [
            {
                "name": rg.name,
                "location": rg.location,
                "resource_group": rg.name,
                "az_cli": f"az group delete -n {rg.name} --yes --no-wait"
            }
            for rg in self.resource_client.resource_groups.list()
            if not list(self.resource_client.resources.list_by_resource_group(rg.name))
        ]

    def get_stopped_vms(self):
        return [
            {
                "name": vm.name,
                "resource_group": vm.id.split("/")[4],
                "location": vm.location,
                "az_cli": f"az vm deallocate --name {vm.name} --resource-group {vm.id.split('/')[4]}"
            }
            for vm in self.compute_client.virtual_machines.list_all()
            if vm.instance_view and any(s.code == "PowerState/stopped" for s in vm.instance_view.statuses)
        ]

    def get_unused_load_balancers(self):
        return [
            {
                "name": lb.name,
                "resource_group": lb.id.split("/")[4],
                "location": lb.location,
                "az_cli": f"az network lb delete -g {lb.id.split('/')[4]} -n {lb.name}"
            }
            for lb in self.network_client.load_balancers.list_all()
            if not lb.frontend_ip_configurations and not lb.backend_address_pools
        ]

    def get_stopped_webapps(self):
        return [
            {
                "name": app.name,
                "resource_group": app.resource_group,
                "location": app.location,
                "az_cli": f"az webapp delete -g {app.resource_group} -n {app.name}"
            }
            for app in self.web_client.web_apps.list()
            if app.state == "Stopped"
        ]

    def get_empty_dns_zones(self):
        return [
            {
                "name": zone.name,
                "resource_group": zone.id.split("/")[4],
                "az_cli": f"az network dns zone delete -g {zone.id.split('/')[4]} -n {zone.name}"
            }
            for zone in self.dns_client.zones.list()
            if not list(self.dns_client.record_sets.list_by_dns_zone(zone.id.split("/")[4], zone.name))
        ]

    def get_unused_route_tables(self):
        return [
            {
                "name": rt.name,
                "resource_group": rt.id.split("/")[4],
                "az_cli": f"az network route-table delete -g {rt.id.split('/')[4]} -n {rt.name}"
            }
            for rt in self.network_client.route_tables.list_all()
            if not rt.subnets
        ]

    def get_unused_gateways(self):
        return [
            {
                "name": gw.name,
                "resource_group": gw.id.split("/")[4],
                "az_cli": f"az network application-gateway delete -g {gw.id.split('/')[4]} -n {gw.name}"
            }
            for gw in self.network_client.application_gateways.list_all()
            if not gw.frontend_ip_configurations
        ]

    def get_empty_backup_vaults(self):
        vaults = [
            res for res in self.resource_client.resources.list()
            if res.type == "Microsoft.RecoveryServices/vaults"
        ]
        results = []
        for vault in vaults:
            rg = vault.id.split("/")[4]
            name = vault.name
            try:
                items = list(self.backup_client.backup_protected_items.list(rg, name))
                if not items:
                    results.append({
                        "name": name,
                        "resource_group": rg,
                        "az_cli": f"az backup vault delete -g {rg} -n {name}"
                    })
            except Exception as e:
                print(f"⚠️ Skipping {name} due to error: {e}")
        return results

    def get_unused_acrs(self):
        return [
            {
                "name": acr.name,
                "resource_group": acr.id.split("/")[4],
                "az_cli": f"az acr delete -g {acr.id.split('/')[4]} -n {acr.name}"
            }
            for acr in self.acr_client.registries.list()
            if acr.login_server is None
        ]

    def generate_cleanup_report(self):
        return {
            "public_ips": self.get_unused_public_ips(),
            "nics": self.get_unattached_nics(),
            "nsgs": self.get_orphaned_nsgs(),
            "disks": self.get_unattached_disks(),
            "resource_groups": self.get_empty_resource_groups(),
            "stopped_vms": self.get_stopped_vms(),
            "load_balancers": self.get_unused_load_balancers(),
            "web_apps": self.get_stopped_webapps(),
            "dns_zones": self.get_empty_dns_zones(),
            "route_tables": self.get_unused_route_tables(),
            "app_gateways": self.get_unused_gateways(),
            "backup_vaults": self.get_empty_backup_vaults(),
            "acr_registries": self.get_unused_acrs()
        }


def display_section(title, items):
    print(f"\n📂 {title} ({len(items)})")
    print("-" * (len(title) + 12))
    for item in items:
        print(f"• {item['name']} | RG: {item['resource_group']}")
        print(f"  💻 az CLI: {item['az_cli']}\n")


def main():
    print("🚀 Starting AzureCleaner Scan...")
    credential = AzureCliCredential()
    sub_client = SubscriptionClient(credential)
    subscriptions = list(sub_client.subscriptions.list())

    print("📋 Available Subscriptions:")
    for idx, sub in enumerate(subscriptions):
        print(f"[{idx + 1}] {sub.display_name} ({sub.subscription_id})")

    print("[0] All Subscriptions")
    selection = input("Select a subscription by number (or 0 for all): ")
    try:
        selected_index = int(selection.strip())
        if selected_index == 0:
            selected_subs = subscriptions
        else:
            selected_subs = [subscriptions[selected_index - 1]]
    except (ValueError, IndexError):
        print("❌ Invalid selection.")
        return
    print("🚀 Starting AzureCleaner Multi-Subscription Scan...")
    credential = AzureCliCredential()
    sub_client = SubscriptionClient(credential)
    subscriptions = list(sub_client.subscriptions.list())

    try:
        for sub in selected_subs:
            print(f"\n🔍 Scanning subscription: {sub.display_name} ({sub.subscription_id})")
            scanner = CleanAzureScanner(subscription_id=sub.subscription_id)
            results = scanner.generate_cleanup_report()

            live_cost = scanner.get_live_cost_summary()
            if live_cost is not None:
                print(f"📊 Current Subscription Cost (Live): ${live_cost:.2f}")

            for key, resources in results.items():
                display_section(key.replace('_', ' ').title(), resources)

    except Exception as e:
        print(f"❌ Scan Failed: {e}")


if __name__ == "__main__":
    main()