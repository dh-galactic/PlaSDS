<script lang="ts">
    import * as Dialog from '$lib/components/ui/dialog/index'
    import  Button from '$lib/components/ui/button/button.svelte'
    export let open = false
    export let openLog =() => {}
    export let clearLog =() => {}
</script>
<Dialog.Root bind:open>
    <Dialog.Content>
        <Dialog.Header>
            <Dialog.Title>Unfinished Run Found</Dialog.Title>
            <Dialog.Description>Do you want to continue the run?</Dialog.Description>
        </Dialog.Header>
        <Dialog.Footer> 
            <Button on:click={() => {
                open = false
                clearLog()
            }}>No</Button>
            <Button on:click={() => {
                open = false
                openLog()
            }}>Yes</Button>
        </Dialog.Footer>
    </Dialog.Content>
</Dialog.Root>