<script lang="ts">
	import type { RackType } from './../lib/runTypes.ts';
    import type { CommandBlock, RunSettings } from "$lib/runTypes";
    import Input from "$lib/components/ui/input/input.svelte";
    import Label from "$lib/components/ui/label/label.svelte";
    import * as Select from "$lib/components/ui/select";
    import RunTable from "./RunTable.svelte";
    import * as Slider from "$lib/components/ui/slider";
    import Button from "$lib/components/ui/button/button.svelte";
    import { controllerCommand } from "$lib/comms";
    import { settings, runState, run } from "$lib/stores/settingsStore";

   

    let runTable : RunTable

    export function resetRun(volume: number): CommandBlock[][] {
        return runTable.resetRun(volume) // TODO: move function here
	}

    const rackSelectTypes  = [
        { value: "5x12", label: "5 x 12" },
        { value: "6x15", label: "6 x 15" }
    ];


    let selectedRackSelectType = rackSelectTypes[0];

    const rackTypes : RackType[] = [
        { description: "5x12", col:5,row:12 },
        { description: "6x15", col:6, row:15}
    ];
    
    $: $settings.rackType = rackTypes.find((rt) => rt.description === selectedRackSelectType.value) || rackTypes[0];
    
    let xlr8 = false;
    let maxRacks = 4;
    if (xlr8) {
        maxRacks = 8;
    }

    type ValueLabel = { value: number; label: string };
    let rackSelections: ValueLabel[] = [];
    for (let index = 1; index <= maxRacks; index++) {
        rackSelections.push({ value: index, label: index.toString() });
    }
    let numRacks = rackSelections[3];
    $: $settings.numRacks = numRacks ? numRacks.value : 4;

    let syringeSizes = [
        { value: 500, label: "500" },
        { value: 1000, label: "1000" },
        { value: 2500, label: "2500" },
        { value: 5000, label: "5000" },
        { value: 10000, label: "10000" },
        { value: 25000, label: "25000" },
        { value: 50000, label: "50000" },
    ];
    let syringeSizeSelected = syringeSizes[4];

    type syringeSpeedsType = {
        [key: string]: {
            minimum: number;
            recommended: number;
            maximum: number;
        };
    };
    let syringeSpeeds: syringeSpeedsType = {
        "500": { minimum: 125, recommended: 250, maximum: 325 },
        "1000": { minimum: 250, recommended: 500, maximum: 650 },
        "2500": { minimum: 300, recommended: 625, maximum: 1250 },
        "5000": { minimum: 625, recommended: 1250, maximum: 2500 },
        "10000": { minimum: 1250, recommended: 2500, maximum: 5000 },
        "25000": { minimum: 1500, recommended: 3125, maximum: 6000 },
        "50000": { minimum: 1500, recommended: 3125, maximum: 6000 },
    };

    let syringeSpeedSelected: number[] = [50];

    function deriveSpeed(syringeSize: number, percent: number) {
        const syringeSpeed = syringeSpeeds[syringeSize];
        if (syringeSpeed === undefined) {
            return 0;
        }
        let speed: number;
        if (percent > 50) {
            percent = (percent - 50) / 50;
            speed =
                percent * (syringeSpeed.maximum - syringeSpeed.recommended) +
                syringeSpeed.recommended;
        } else {
            percent = percent === 0 ? 0 : percent / 50;
            speed =
                percent * (syringeSpeed.recommended - syringeSpeed.minimum) +
                syringeSpeed.minimum;
        }
        return Math.floor(speed);
    }
    function deriveSpeedPercent(syringeSize: number, speed: number): number {
        const syringeSpeed = syringeSpeeds[syringeSize];
        if (syringeSpeed === undefined) {
            return 0;
        }

        let percent: number;
        if (speed > syringeSpeed.recommended) {
            percent =
                50 +
                ((speed - syringeSpeed.recommended) /
                    (syringeSpeed.maximum - syringeSpeed.recommended)) *
                    50;
        } else {
            percent =
                ((speed - syringeSpeed.minimum) /
                    (syringeSpeed.recommended - syringeSpeed.minimum)) *
                50;
        }

        return Math.floor(percent);
    }

    $: $settings.speed = deriveSpeed(
        syringeSizeSelected.value,
        syringeSpeedSelected[0],
    );
    $: $settings.syringeSize = syringeSizeSelected.value;

    export function setSettings(settings: RunSettings) { 
        $settings = settings;
        syringeSizeSelected = syringeSizes.find(
            (ss) => ss.value == settings.syringeSize,
        );
        syringeSpeedSelected = [
            deriveSpeedPercent(settings.syringeSize, settings.speed),
        ];
        numRacks = rackSelections[settings.numRacks - 1];
    }
    let flushes : number = 1; 
    function flush(){
        if (flushes>0 && flushes <100){
            controllerCommand('flush',{flushes:flushes})
        }
    }
    
    $: running = ($runState.status !== "Idle") && ($runState.status !== "Finished");
</script>
<div class="flex flex-col space-y-1 m-0 p-0">
    <div class="m-0 p-2 border-2 rounded-md">    
            <div class="flex flex-row justify-center px-2 space-x-5">
                <div class="flex flex-col w-1/4">
                    <div class="flex flex-row justify-between w-full">
                        <Label class="text-xl w-1/2 p-2" for="numberRacks"
                            >Racks</Label
                        >
                        <Select.Root
                            disabled={running}
                            bind:selected={numRacks}
                        >
                            <Select.Trigger class="ring-10  w-1/2">
                                <Select.Value
                                    class="text-lg"
                                    placeholder="Number Racks"
                                />
                            </Select.Trigger>
                            <Select.Content>
                                {#each rackSelections as rackSelection}
                                    <Select.Item
                                        value={rackSelection.value}
                                        class="text-lg"
                                        >{rackSelection.label}</Select.Item
                                    >
                                {/each}
                            </Select.Content>
                        </Select.Root>
                    </div>
                    <div class="flex flex-row bg-blue">
                        <Label class="text-xl p-2 w-1/2" for="rackSize"
                            >Rack Size</Label
                        >
                        <Select.Root
                            disabled={running}
                            bind:selected={selectedRackSelectType}
                        >
                            <Select.Trigger class="ring-10 w-1/2 ">
                                <Select.Value
                                    class="text-lg"
                                    placeholder="Rack Type"
                                />
                            </Select.Trigger>
                            <Select.Content>
                                {#each rackSelectTypes as rackType}
                                    <Select.Item
                                        value={rackType.value}
                                        class="text-lg"
                                        >{rackType.label}</Select.Item
                                    >
                                {/each}
                            </Select.Content>
                        </Select.Root>
                    </div>
                </div>
                <div class="flex flex-col w-1/4">
                    <div class="flex flex-row justify-between">
                        <Label class="text-lg w-1/2 p-2" for="syringSize"
                            >Syringe Size μL</Label
                        >
                        <Select.Root
                            disabled={running}
                            bind:selected={syringeSizeSelected}
                            onSelectedChange={() =>
                                (syringeSpeedSelected = [50])}
                        >
                            <Select.Trigger
                                class="pl-5 ring-10 text-right w-1/2 "
                            >
                                <Select.Value
                                    class=" text-lg text-right"
                                    placeholder="Syringe Size"
                                />
                            </Select.Trigger>
                            <Select.Content class="items-left">
                                {#each syringeSizes as syringeSize}
                                    <Select.Item
                                        value={syringeSize.value}
                                        class="text-lg "
                                        >{syringeSize.label}</Select.Item
                                    >
                                {/each}
                            </Select.Content>
                        </Select.Root>
                    </div>
                    <div class="flex flex-row justify-between ">
                        <Label class="text-lg w-3/4  p-2" for="numberRacks"
                            >Dispense Depth (mm)</Label
                        >
                        <Input
                            type="number"
                            max={150}
                            min={0}
                            disabled={running}
                            bind:value={$settings.probeDepth}
                            class="text-lg w-1/4  invalid:text-red-500"
                        />
                    </div>
                </div>
                <div class="flex flex-col w-1/4">
                    <Label
                        class="text-xl px-2 w-full text-center"
                        for="syringSize">Pump Speed</Label
                    >
                    <div class="flex flex-row w-full text-center">
                        <div class="px-2 w-full">
                            {$settings.speed} μL/s
                            <Slider.Root
                                disabled={running}
                                class="w-full p-1"
                                bind:value={syringeSpeedSelected}
                                min={0}
                                max={100}
                                step={1}
                            ></Slider.Root>
                        </div>
                    </div>
                </div>
                <div class="flex flex-col w-1/4 justify-center items-center space-y-1">
                    <div class="flex flex-row w-2/3 justify-between items-center">
                        <Label class="text-lg min-w-[150px]">Flushes After Run</Label>
                        <Input bind:value={$settings.flushAfter} min={1} max={100} placeholder="# of Flushes after run" class="invalid:text-red-500 text-lg  invalid:font-bold text-right pr-5 max-w-[80px] min-w-[50px]"></Input>
                    </div>
                    <div class="flex flex-row w-2/3 ">
                        <Input bind:value={flushes} min={0} max={100} placeholder="# of Flushes" class="text-right text-lg pr-5 min-w-[50px] rounded-r-none"></Input>
                        <Button on:click={flush} class="rounded-l-none text-lg">FLUSH</Button>
                    </div>
                    
                </div>
            </div>
            <RunTable bind:this={runTable}  numRacks={numRacks.value} ></RunTable>
    </div>
</div>
