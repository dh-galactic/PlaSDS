<script lang="ts">

import { run, settings, filename, runError, runState, connections } from "$lib/stores/settingsStore";
import Button from "$lib/components/ui/button/button.svelte";
import { controllerCommand } from "$lib/comms"

$connections = {
	autosampler: "Disconnected",
	hamilton: "Disconnected",
};

function connect() { 
	$connections.autosampler = "Disconnected";
	$connections.hamilton = "Disconnected";

	controllerCommand("connect").then((data) => {
		console.log(data);
		if ((data.result = "connected")) {
			for (let device of data.devices) {
				if (
					device.device == "ASX-560" ||
					device.device == "ASX-520"
				) {
					$connections.autosampler = "Connected";
				}
				if (device.device == "Hamilton 600") {
					$connections.hamilton = "Connected";
				}
			}
			if ($connections.autosampler == "Disconnected" ||	$connections.hamilton == "Disconnected"	) {
                $runError = {
					error: true,
					type:"Device Connection Error",
					description: "Unable to connect to" +
					($connections.autosampler == "Disconnected"	? "" : " Autosampler") +
					($connections.hamilton == "Disconnected" ? "" :	" Hamilton") +
					" - Check Power and Cables",
				}
			}
		} else {
			$runError = {
				error: true,
				type: "Controller Connection Error",
				description: "Unable to Connect to controller. Try Restarting Controller",
			}
		}
	})
}

function initialize() {
	controllerCommand("initialize").then((data) => {
		console.log(data.connections)
		$connections = data.connections;
		if (data.error) {
			$runError = {
				error: true,
				type: "Initialisation Error",
				description: data.errorCode
			} 
		} else {
			$runError = {
				error: false,
				type: '',
				description: ''
			}
			if ($runState?.status == "Error") {
				$runState.status = "Idle";
			}
		}
	});
}

function pauseRun() {
	controllerCommand("pause").then((data) => {
		if (data.result != "paused") {
			$runError = {
				error: true,
				type: "Connection Error",
				description: "Error Pausing"
			}
		} else {
			$runState.status = "Paused";
		}
	});
}
function runRun(fromLog = false) {
	if (fromLog) {
		controllerCommand("runFromLog").then((data) => {
			if (data.result != "started") {
				$runError = {
					error: true,
					type: "Run Error",
					description: data.errorCode
				}
			} else {
				$filename = data.fileName;
				checkrunState();
			}
		});
	} else {
		controllerCommand("run", { run: $run, settings: $settings }).then(
			(data) => {
				if (data.result != "started") {
					$runError = {
						error: true,
						type: "Run Error",
						description: data.errorCode
					}
				} else {
					checkrunState();
				}
			},
		);
	}
}
const checkrunState = async () => {
	$runState.status = "Running";
	while ($runState.status == "Running") {
		try {
			const data = await controllerCommand("runState");
			$runState = data;
			if (data.status == "Finished") {
				break;
			}
			if (data.status == "Error") {
				$runError = {
					error: true,
					type: "Run Error",
					description: data.errorCode
				}
				break;
			}
		} catch (error) {
			$runError = {
					error: true,
					type: "Communication Fetch Error",
					description: 'Error Checking Run Status'
				} 
			break;
		}
		await new Promise((resolve) => setTimeout(resolve, 500));
	}
};
	

</script>

<div class="flex flex-col space-y-2 m-2">
	<div
		class="flex flex-row justify-end items-center space-x-2 p-2 rounded-md border-2"
	>
		<div class="flex flex-col space-y-2">
			{#if $connections.autosampler == "Disconnected" || $connections.hamilton == "Disconnected"}
				<Button
					size="lg"
					class=" rounded-sm h-[30px] p-3 text-xl"
					on:click={connect}
				>
					CONNECT
				</Button>
			{:else}
				<Button
					size="lg"
					class=" rounded-sm h-[30px] p-3 text-xl"
					on:click={initialize}
				>
					INITIALISE
				</Button>
			{/if}
			{#if $connections.autosampler == "Initialized" && $connections.hamilton == "Initialized"}
				{#if $runState?.status == "Idle"}
					<Button
						size="lg"
						class=" rounded-sm h-[30px] p-3 text-xl"
						on:click={() => runRun(false)}
					>
						START
					</Button>
				{:else if $runState?.status == "Running"}
					<Button
						size="lg"
						class=" rounded-sm h-[30px] p-3 text-xl"
						on:click={pauseRun}
					>
						PAUSE
					</Button>
				{:else if $runState?.status == "Paused"}
					<Button
						size="lg"
						class=" rounded-sm h-[30px] p-3 text-xl"
						on:click={() => runRun(true)}
					>
						CONTINUE
					</Button>
				{/if}
				{#if $runState?.status == "Finished" || $runState?.status == "Paused"}
					<Button
						size="lg"
						class=" rounded-sm h-[30px] p-3 text-xl"
						on:click={() => ($runState.status = "Idle")}
					>
						RESET
					</Button>
				{/if}
			{/if}
		</div>
		<div>
			<div
				class="flex flex-row items-center justify-end text-lg p-1
                 rounded-sm"
			>
				AUTOSAMPLER
				<svg height="20" width="20" class="mx-2">
					<circle
						r="9"
						cx="10"
						cy="10"
						fill={$connections.autosampler == "Disconnected"
							? "red"
							: $connections.autosampler == "Initialized"
								? "green"
								: "gold"}
					/>
				</svg>
			</div>
			<div
				class="flex flex-row items-center justify-end text-lg p-1
                rounded-sm"
			>
				HAMILTON
				<svg height="20" width="20" class="mx-2">
					<circle
						r="9"
						cx="10"
						cy="10"
						fill={$connections.hamilton == "Disconnected"
							? "red"
							: $connections.hamilton == "Initialized"
								? "green"
								: "gold"}
					/>
				</svg>
			</div>
		</div>
	</div>
</div>
