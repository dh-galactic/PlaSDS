<script lang="ts">

	import { Button } from "$lib/components/ui/button";
	import RunCard from "./RunCard.svelte";
	import RunStatusCard from "./RunStatusCard.svelte";
	import type {  RunData} from "$lib/runTypes.js";
	import {
		settings,
		run,
		runState,
		filename,
		connections,
		runError,
		controllerIP
	} from "$lib/stores/settingsStore";
	import FileBox from "./FileBox.svelte";
	import { onMount } from "svelte";
	import RestartDialog from "./RestartDialog.svelte";
	import ErrorDisplay from "./ErrorDisplay.svelte";
	import Connections from "./ConnectionsBox.svelte";
    import ConnectionsBox from "./ConnectionsBox.svelte";
	import {controllerCommand} from "$lib/comms"

	//TODO: IP Settings
	//
	

	let debug = false;
	
	let runcard: RunCard;
	let connectionsBox : ConnectionsBox;

	let logRun: RunData | null = null;

	onMount(() => {
		$controllerIP = location.hostname;
		console.log("Controller IP", $controllerIP);
		async function newPage() {
			const data = await controllerCommand("reloadStatus");

			if (data == undefined) {
				$runError = {
					error: true,
					type: "Connection Error",
					description: "No connection to controller",
				}
			} else if (data.result == "Error") {
				$runError = {
					error: true,
					type: "Connection Error",
					description: "Connection - " + data.errorCode,
				}
			} else if (data.runState) {
				logRun = data;
				if (
					data.runState.status != "Finished" &&
					data.runState.status != "Idle"
				) {
					logRunDialogOpen = true;
				}
				$connections = data.connections;
			}
		}
		newPage();
		
		return () => {};
	});

	let logRunDialogOpen = false;

	function openLog() {
		if (logRun) {
			$settings = logRun.settings;
			$runState = logRun.runState;
			$run = logRun.run;
			$filename = logRun.fileName;
			if ($runState.status == "Running") {
				connectionsBox.checkrunState();
			}
		}
	}

	function clearLog() {
		controllerCommand("clearLog").then((data) => {
			if (data.result != "cleared") {
				console.error("Error Clearing Log", data.errorCode);
			}
		});
		logRun = null;
	}

</script>

<RestartDialog {openLog} {clearLog} bind:open={logRunDialogOpen}/>
<div class="flex flex-col justify-center items-center space-y-4">
	<ErrorDisplay {connectionsBox} />
	<div class="w-11/12">
		<div class="flex flex-row space-x-5 justify-between w-full">
			<FileBox {runcard}></FileBox>
			<Connections bind:this={connectionsBox} />
		
		</div>
		<RunStatusCard></RunStatusCard>
		<RunCard bind:this={runcard}></RunCard>
	</div>
</div>

<div class="{debug ? '' : 'hidden'}">
	Status -{$runState?.status}<br />
	as-{$connections.autosampler}<br />
	ham-{$connections.hamilton}<br />
</div>
