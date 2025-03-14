<script>
    import NetworkSettings from "./NetworkSettings.svelte";
    import * as Dialog from "$lib/components/ui/dialog/index";
    import { Content } from "$lib/components/ui/accordion";
    import Settings  from "lucide-svelte/icons/settings";
    import * as DropdownMenu from "$lib/components/ui/dropdown-menu";
  

    
    let nsOpen = false;
</script>
<div class="flex flex-row items-start justify-between w-full">
    <div class="w-1/4">
        <img src="/RectangleLogo.png" class="max-h-[60px]" alt="Galactic Scientific"/>
    </div>
    <div>
        <Settings />
        <NetworkSettings bind:dialogOpen={nsOpen} />
    </div>
</div>
<div class="flex items-center">
<div class="w-full"><slot></slot></div></div>

