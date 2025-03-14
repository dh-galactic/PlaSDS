<script lang="ts">
import IPInput from './IPInput.svelte';
import * as Dialog from "$lib/components/ui/dialog/index";
import * as Select from "$lib/components/ui/select/index";
import Button from "$lib/components/ui/button/button.svelte";
import { controllerCommand } from '$lib/comms';
import { controllerIP } from '$lib/stores/settingsStore';
import { onMount } from 'svelte';
    import Switch from '$lib/components/ui/switch/switch.svelte';

let dhcpServer = false
export let dialogOpen = false


function cancel(){
    dialogOpen = false

}
function save(){
    if (networkSelected.value == 'DHCP'){
        let data = {
                type:'dynamic',
        }
        controllerCommand('changeIP',data).then((response)=>{
                console.log(response)
        })
    } else if (networkSelected.value == 'Static'){
        let data = {
            type:'static',
            ip: ip.join('.'),
            netmask:ipNM.join('.'),
            gateway:ipG.join('.')
        }
        controllerCommand('changeIP',data).then((response)=>{
            console.log(response)
        })
    }  
    
    dialogOpen = false
}

let ip=[192,168,1,1]

onMount(()=>{
    controllerCommand('nslookup').then((data)=>{

        if (data.type == 'dynamic'){
            networkSelected = {value:'DHCP',label:'Automatic(DHCP)'}
        } else if (data.type == 'static'){
            console.log('Static')
        
            networkSelected = {value:'Static',label:'Static'}
            dhcpServer = data.dhcp
            ip = data.ip
            ipNM = data.netmask
            ipG = data.gateway
        }
    })
})


let ipNM=[255,255,255,0]
let ipG=[192,168,1,1]
let networkSelected = {value:'DHCP',label:'Automatic(DHCP)'}

</script>
<Dialog.Root bind:open={dialogOpen}>
    <Dialog.Trigger>
    </Dialog.Trigger>
     
    <Dialog.Content class="w-3/5">
            <Select.Root bind:selected={networkSelected}>
                <Select.Trigger class="w-[300px]">
                  <Select.Value placeholder="" />
                </Select.Trigger>
                <Select.Content>
                  <Select.Group>
                        <Select.Item value='DHCP' label='Automatic(DHCP)' />
                        <Select.Item value='Static' label='Static' />
                  </Select.Group>
                </Select.Content>
            </Select.Root>
            {#if networkSelected.value == 'Static'}
                <IPInput bind:ip={ip}>IP Address</IPInput>
                <IPInput bind:ip={ipNM}>Netmask</IPInput>
                <IPInput bind:ip={ipG}>Gateway</IPInput>
                <Switch bind:checked={dhcpServer}></Switch>Run Controller as DHCP server
            {/if}

        <Dialog.Footer>
            <Button on:click={cancel} class="">Cancel</Button>
            <Button on:click={save} class="">Save</Button>
        </Dialog.Footer>
    </Dialog.Content>
</Dialog.Root>
