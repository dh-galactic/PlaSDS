<script lang="ts">

import Label from "$lib/components/ui/label/label.svelte";


export let ip = [0,0,0,0]


function validate(ev) {
    const target = ev.target as HTMLInputElement;
    let part = target.value
    console.log(part)
    part = part.replace(/[^0-9]/g, '');
    // If the length of the passed string is more than 3, it is not valid
    if (part.length > 3) {
        part = part.slice(0,3);
    }

    // Convert the string to an integer
    let numpart = parseInt(part);
    // The string is valid if the number generated is between 0 to 255
    numpart = numpart > 255 ? 255 : numpart  
    numpart = numpart < 0 ? 0 : numpart
    ev.target.value = numpart
}
 
</script>

<div class="flex flex-col">
    <Label class="text-lg"><slot></slot></Label>
    <div class="flex flex-row items-end ">
        <input type="number" on:input={validate} bind:value={ip[0]} id="ip1" class="m-2 ring-1 w-[60px] text-right px-1 "/>.
        <input type="number" on:input={validate} bind:value={ip[1]} id="ip2" class="m-2 ring-1 w-[60px] text-right px-1 "/>.
        <input type="number" on:input={validate} bind:value={ip[2]} id="ip3" class="m-2 ring-1 w-[60px] text-right px-1 "/>.
        <input type="number" on:input={validate} bind:value={ip[3]} id="ip4" class="m-2 ring-1 w-[60px] text-right px-1 "/>
    </div>
</div>

