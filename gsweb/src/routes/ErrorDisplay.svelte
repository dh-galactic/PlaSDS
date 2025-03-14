<script lang="ts">
    import type { RunError } from '$lib/runTypes';
	import { runError } from '$lib/stores/settingsStore'
	import ConnectionsBox from './ConnectionsBox.svelte';

	export let connectionsBox :ConnectionsBox;

	$: $runError = processRunError($runError)

	function processRunError(re : RunError){
		if (re.type == 'Pause Error'){
			connectionsBox.pauseRun()
		}
		return re
	}

</script>
{#if $runError.error}
		<div
			class="border-2 p-3 bg-red-100 border-red-400 text-2xl flex flex-col items-center space-y-3"
		>
			{$runError.type}<br />
			{$runError.description}
			<!-- <Button on:click={resetHamilton}>Reset Hamilton</Button> -->
		</div>
{/if}