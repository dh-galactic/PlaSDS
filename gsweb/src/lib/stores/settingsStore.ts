import { writable} from 'svelte/store';
import type { Writable } from 'svelte/store';
import type { RunSettings, RunState, CommandBlock, ConnectionStatus, RunError} from '$lib/runTypes';

const ipDefault = "192.168.1.1"

export let settings : Writable<RunSettings> = writable({
	numRacks: 4,
	probeDepth: 100,
	speed: 2500,
	syringeSize: 10000,
	rackType: {
		col: 5,
		row: 12,
		description: '5x12'
	},
	flushAfter: 1
});

export let runState: Writable<RunState> =  writable({ 
	status: 'Idle',
	currentStep: 0,
	totalSteps: 0,
	startTime: new Date(),
});

export let connections: Writable<ConnectionStatus> = writable({
	autosampler: "Disconnected",
	hamilton: "Disconnected",
});

export let run: Writable<Array<Array<CommandBlock>>> = writable([]);

export let filename: Writable<string> = writable('');

export let runError:Writable<RunError> = writable({
	error: false,
	type: '',
	description: ''
});

export let controllerIP: Writable<string> = writable(ipDefault);