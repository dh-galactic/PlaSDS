<script lang="ts">
	
    import * as Table from "$lib/components/ui/table";
    import Input from "$lib/components/ui/input/input.svelte";
    import type { CommandBlock, AutoSamplerPosition } from "$lib/runTypes";
    import Button from "$lib/components/ui/button/button.svelte";
    export let rackNumber :number;


    let maxPostion = 60
    let blocks : CommandBlock[][] = new Array(4).fill([{
            startPosition: 1,
            endPosition: maxPostion,
            volume: 0,
            waitSeconds: 0
    }])
    
    function newBlock(blockToAdd:CommandBlock){
        let newStartPosition = blockToAdd[blockToAdd.length -1].endPosition + 1 
        newStartPosition = newStartPosition > maxPostion ? maxPostion : newStartPosition
        
        blockToAdd.push({
            startPosition: newStartPosition,
            endPosition: maxPostion,
            volume: blockToAdd[blockToAdd.length-1].volume,
            waitSeconds: blockToAdd[blockToAdd.length -1].waitSeconds
        })
        console.log(blockToAdd)
    }

</script>

  

