
## CATO-CLI - mutation.policy.socketLan.updateRule:
[Click here](https://api.catonetworks.com/documentation/#mutation-mutation.policy.socketLan.updateRule) for documentation on this operation.

### Usage for mutation.policy.socketLan.updateRule:

```bash
catocli mutation policy socketLan updateRule -h

catocli mutation policy socketLan updateRule <json>

catocli mutation policy socketLan updateRule "$(cat < mutation.policy.socketLan.updateRule.json)"

catocli mutation policy socketLan updateRule '{"socketLanPolicyMutationInput":{"policyMutationRevisionInput":{"id":"id"}},"socketLanUpdateRuleInput":{"id":"id","socketLanUpdateRuleDataInput":{"description":"string","destination":{"floatingSubnet":{"by":"ID","input":"string"},"globalIpRange":{"by":"ID","input":"string"},"group":{"by":"ID","input":"string"},"host":{"by":"ID","input":"string"},"ip":["example1","example2"],"ipRange":{"from":"example_value","to":"example_value"},"networkInterface":{"by":"ID","input":"string"},"siteNetworkSubnet":{"by":"ID","input":"string"},"subnet":["example1","example2"],"systemGroup":{"by":"ID","input":"string"},"vlan":["example1","example2"]},"direction":"TO","enabled":true,"name":"string","nat":{"enabled":true,"natType":"DYNAMIC_PAT"},"service":{"custom":{"port":["example1","example2"],"portRange":{"from":"example_value","to":"example_value"},"protocol":"ANY"},"simple":{"name":"HTTP"}},"site":{"group":{"by":"ID","input":"string"},"site":{"by":"ID","input":"string"}},"source":{"floatingSubnet":{"by":"ID","input":"string"},"globalIpRange":{"by":"ID","input":"string"},"group":{"by":"ID","input":"string"},"host":{"by":"ID","input":"string"},"ip":["example1","example2"],"ipRange":{"from":"example_value","to":"example_value"},"networkInterface":{"by":"ID","input":"string"},"siteNetworkSubnet":{"by":"ID","input":"string"},"subnet":["example1","example2"],"systemGroup":{"by":"ID","input":"string"},"vlan":["example1","example2"]},"transport":"WAN"}}}'

catocli mutation policy socketLan updateRule '{
    "socketLanPolicyMutationInput": {
        "policyMutationRevisionInput": {
            "id": "id"
        }
    },
    "socketLanUpdateRuleInput": {
        "id": "id",
        "socketLanUpdateRuleDataInput": {
            "description": "string",
            "destination": {
                "floatingSubnet": {
                    "by": "ID",
                    "input": "string"
                },
                "globalIpRange": {
                    "by": "ID",
                    "input": "string"
                },
                "group": {
                    "by": "ID",
                    "input": "string"
                },
                "host": {
                    "by": "ID",
                    "input": "string"
                },
                "ip": [
                    "example1",
                    "example2"
                ],
                "ipRange": {
                    "from": "example_value",
                    "to": "example_value"
                },
                "networkInterface": {
                    "by": "ID",
                    "input": "string"
                },
                "siteNetworkSubnet": {
                    "by": "ID",
                    "input": "string"
                },
                "subnet": [
                    "example1",
                    "example2"
                ],
                "systemGroup": {
                    "by": "ID",
                    "input": "string"
                },
                "vlan": [
                    "example1",
                    "example2"
                ]
            },
            "direction": "TO",
            "enabled": true,
            "name": "string",
            "nat": {
                "enabled": true,
                "natType": "DYNAMIC_PAT"
            },
            "service": {
                "custom": {
                    "port": [
                        "example1",
                        "example2"
                    ],
                    "portRange": {
                        "from": "example_value",
                        "to": "example_value"
                    },
                    "protocol": "ANY"
                },
                "simple": {
                    "name": "HTTP"
                }
            },
            "site": {
                "group": {
                    "by": "ID",
                    "input": "string"
                },
                "site": {
                    "by": "ID",
                    "input": "string"
                }
            },
            "source": {
                "floatingSubnet": {
                    "by": "ID",
                    "input": "string"
                },
                "globalIpRange": {
                    "by": "ID",
                    "input": "string"
                },
                "group": {
                    "by": "ID",
                    "input": "string"
                },
                "host": {
                    "by": "ID",
                    "input": "string"
                },
                "ip": [
                    "example1",
                    "example2"
                ],
                "ipRange": {
                    "from": "example_value",
                    "to": "example_value"
                },
                "networkInterface": {
                    "by": "ID",
                    "input": "string"
                },
                "siteNetworkSubnet": {
                    "by": "ID",
                    "input": "string"
                },
                "subnet": [
                    "example1",
                    "example2"
                ],
                "systemGroup": {
                    "by": "ID",
                    "input": "string"
                },
                "vlan": [
                    "example1",
                    "example2"
                ]
            },
            "transport": "WAN"
        }
    }
}'
```

#### Operation Arguments for mutation.policy.socketLan.updateRule ####

`accountId` [ID] - (required) N/A    
`socketLanPolicyMutationInput` [SocketLanPolicyMutationInput] - (required) N/A    
`socketLanUpdateRuleInput` [SocketLanUpdateRuleInput] - (required) N/A    
