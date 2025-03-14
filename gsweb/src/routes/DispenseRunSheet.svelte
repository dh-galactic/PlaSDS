<script lang="ts">
    import * as Table from "$lib/components/ui/table";
    import Input from "$lib/components/ui/input/input.svelte";

    import { getDisplayPosition } from "$lib/utils";
    
    const colHeader = ['Dilutent Position','Dilutent Volume μl'];
</script>
<Table.Root >
    <Table.Header>
        <Table.Row>
            {#each colHeader as headLabel} 
                <Table.Head id={headLabel} class="border-2 text-xl font-bold text-primary" >{headLabel}</Table.Head>
            {/each}
        </Table.Row>
    </Table.Header>
<Table.Body>
{#each sl as seqLine, i}  
    <Table.Row>
        {#if seqLine.dispense != null}
                 
                 <Table.Cell class="border-2 text-lg">{getDisplayPosition(seqLine.dispense.position)}</Table.Cell>
                 <Table.Cell class="border-2 text-lg">
                     <Input class="border-0" type="number" id={i+"dispenseVol"} bind:value={seqLine.dispense.volume} ></Input>
                 </Table.Cell>
            {/if}
        </Table.Row>
        {/each}
    </Table.Body>
</Table.Root>

