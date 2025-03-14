
<script lang="ts">
  import * as Dialog from "$lib/components/ui/dialog";
  import {
    Button,
    buttonVariants
  } from "$lib/components/ui/button/index.js";
  import Label from "$lib/components/ui/label/label.svelte";
  import Input from "$lib/components/ui/input/input.svelte";
    import DialogOverlay from "./ui/dialog/dialog-overlay.svelte";
</script>
 
<Dialog.Root>
  <Dialog.Trigger class={buttonVariants({ variant:'default' })}><span class="text-xl">SETTINGS</span></Dialog.Trigger>
  <Dialog.Content>
    <Dialog.Header>
      <Dialog.Title>Advanced Settings</Dialog.Title>
      </Dialog.Header>
    <Label>Syringe Pump Speed</Label>
    <Input type="number"></Input>
    <div class="flex flex-row space-x-2">
      <Button>Save</Button>
      <Dialog.Close class={buttonVariants({variant:'default'})}>Cancel</Dialog.Close>
    </div> 
  </Dialog.Content>
</Dialog.Root>



