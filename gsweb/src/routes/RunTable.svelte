<script lang="ts">
    import type { RackType } from '$lib/runTypes'
    import Button from '$lib/components/ui/button/button.svelte';
    import type { CommandBlock } from '$lib/runTypes';
    import * as Table from "$lib/components/ui/table";
    import * as Tooltip  from '$lib/components/ui/tooltip/index';
    import { run,settings } from '$lib/stores/settingsStore'
    
    export let numRacks : number
    
  

    
    $run = resetRun(1000)

    $: $run = setRacks(numRacks, $settings.rackType)
    
    $: maxPosition =  $settings.rackType.col * $settings.rackType.row

    export function resetRun(volume:number): CommandBlock[][]{
        maxPosition = $settings.rackType.col * $settings.rackType.row
        let tempRun = new Array(numRacks)
        for (let x = 0; x < numRacks; x++){
            tempRun[x] = [{
                startPosition: 1,
                endPosition: maxPosition,
                volume: volume,
                waitSeconds: 0
            }]
        }
        return tempRun;
    }
    
    function setRacks(numRacks: number,racktype : RackType) : CommandBlock[][]{
        
        maxPosition = racktype.col * racktype.row
        
        if ($run.length < numRacks){
            let diff = numRacks - $run.length
            for (let x = 0; x < diff; x++){
                $run.push([{
                    startPosition: 1,
                    endPosition: maxPosition,
                    volume: $run[$run.length-1][$run[$run.length-1].length-1].volume,
                    waitSeconds: 0
                }])
            }
            
        } else if ($run.length > numRacks){
            let diff = $run.length - numRacks
            for (let x = 0; x < diff; x++){
                $run.pop()
            }
        }
        return $run
    }
    
    function newBlock(rackBlocks: CommandBlock[]){

        let lastIndex = rackBlocks.length - 1
    
        let newStartPosition = rackBlocks[lastIndex].endPosition + 1 

        newStartPosition = newStartPosition > maxPosition ? maxPosition : newStartPosition

        rackBlocks.push({
            startPosition: newStartPosition,
            endPosition: maxPosition,
            volume: rackBlocks[lastIndex].volume,
            waitSeconds: rackBlocks[lastIndex].waitSeconds
        })
        $run = $run
    }
    function deleteBlock(block: CommandBlock, rack: CommandBlock[]){
        let index = rack.indexOf(block)
        if (rack.length > 1){
            rack.splice(index,1)
        }
        $run = $run
    }

    const colHeader = ["Rack","Start Position","End Position","Dispense Volume μl",'Commands'];
    
    function validate(ev){
        ev.target.value = ev.target.value.replace(/[^0-9]/g, '');
    }
    function validateEndPosition(ev,startPos:number){
        validate(ev)
        if(startPos  > ev.target.value){
            ev.target.value = startPos
        }   
    }
    function validateStartPosition(ev,endPos:number){
        validate(ev)
        if(endPos < ev.target.value){
            ev.target.value = endPos
        }   
    }
</script>
<div class=" m-0 p-2 border-0">
        <Table.Root class="m-0 p-0">
            <Table.Header>
                <Table.Row>
                    {#each colHeader as headLabel} 
                        <Table.Head id={headLabel} class="w-1/5 border-2 text-xl font-bold text-primary text-center" >{headLabel}</Table.Head>
                    {/each}
         
                </Table.Row>
            </Table.Header>
        <Table.Body class="border-2">
            {#each $run as rack , rackNumber  }
                {#each rack as block }
                    <Table.Row class="m-0 p-0 {( rackNumber & 1 ) ? "bg-" : " bg-slate-200"} hover:bg-inherit/50">
                        
                        <Table.Cell class="m-0 p-0  border-2 text-lg text-center">
                            <span class="text-lg border-0 bg-transparent rounded-none text-center w-full  focus:outline-0">
                                     {rackNumber + 1}</span>
                        </Table.Cell>
                        <Table.Cell class="m-0 p-0 border-2 text-lg  ">
                            <input on:focus={(ev)=>ev.target.select()} class="invalid:text-red-500 invalid:font-bold text-lg  p-1 px-2 border-0 bg-transparent rounded-none text-center w-full focus:outline-0 focus-visible:outline-1 " 
                                type="number" on:change={(ev)=>validateStartPosition(ev,block.endPosition)}  bind:value={block.startPosition} min=1 max={maxPosition} />
                        </Table.Cell>
                        <Table.Cell class="m-0 p-0 border-2 text-lg">
                            <input id="endPos" on:focus={(ev)=>ev.target.select()} class="invalid:text-red-500  invalid:font-bold text-lg  p-1 px-2 border-0 bg-transparent rounded-none text-center w-full focus:outline-0 focus-visible:outline-1 " 
                                type="number" on:change={(ev)=>validateEndPosition(ev,block.startPosition)} bind:value={block.endPosition} min=1 max={maxPosition}/>
                        </Table.Cell>
                        <Table.Cell class="m-0 p-0 border-2 text-lg">
                            <input on:focus={(ev)=>ev.target.select()} class="invalid:text-red-500  invalid:font-bold text-lg  p-1 px-2 border-0 bg-transparent rounded-none text-center w-full focus:outline-0 focus-visible:outline-1 " 
                                type="number"  on:input={validate}  bind:value={block.volume} min=0 max={$settings.syringeSize}/>
                        </Table.Cell>            
                        <Table.Cell class="p-2 flex flex-row text-center justify-center w-full space-x-2">
                            <Tooltip.Root>
                                <Tooltip.Trigger>
                                    <Button class="text-3xl w-[40px] " variant="outline" on:click={() => newBlock(rack)}>+</Button>
                                </Tooltip.Trigger>
                                <Tooltip.Content> 
                                    <p>Add New Block for Rack {rackNumber +1 }</p>
                                </Tooltip.Content>
                            </Tooltip.Root>

                            <Button class=" {rack.length > 1 ? 'visible' : 'invisible'} text-3xl w-[40px] " variant="outline" on:click={() => deleteBlock(block,rack)}>-</Button>
                        </Table.Cell>
                    </Table.Row>
                {/each} 
            {/each}
        </Table.Body>
    </Table.Root>
</div>