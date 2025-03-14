<script lang="ts">
import Label from "$lib/components/ui/label/label.svelte";
import Input from "$lib/components/ui/input/input.svelte";
import Button from "$lib/components/ui/button/button.svelte";
import { controllerCommand } from "$lib/comms";
import {run, settings} from "$lib/stores/settingsStore";
import * as Dialog from "$lib/components/ui/dialog/index";
import * as Table from "$lib/components/ui/table/index";
import RunCard from "./RunCard.svelte";

export let runcard: RunCard
let fileName: string = "Untitled";

let saveError: boolean = false;

type fileInfo = { name: string; lastModified: string };
let saveFiles: fileInfo[] = [];
let loadFile: { name: string; lastModified: string } | null = null;
let loadDialogOpen = false;
let newVolume: number = 1000;
let newName: string = "Untitiled";


function saveRun(name: string, overwrite: boolean = false) {
		controllerCommand("saveRun", {
			name: name,
			run: $run,
			settings: $settings,
			overwrite: overwrite,
		})
			.then((data) => {
				if (data.result != "saved") {
					saveError = true;
					data.errorCode
						? console.error("Error Saving Run", data.errorCode)
						: null;
					//TODO: LOG ERRORS
				} else {
					saveError = false;
				}
			})
			.catch((error) => console.error("Error", error));
	}
	function loadRun(fN: fileInfo) {
		controllerCommand("loadRun", { file: fN }).then((data) => {
			if (data.result != "loaded") {
				console.error("Error Loading Run", data.errorCode);
			} else {
				$run = data.run;
				runcard.setSettings(data.settings); 
				fileName = fN.name;
			}
		});
	}

	function getSaveFiles() {
		controllerCommand("getSaveFiles")
			.then((data) => {
				saveFiles = data.files;
			})
			.catch((error) => console.error("Error", error));
	}
</script>

<div class="flex flex-col space-x-3 justify-end w-1/2">
    <div>
        <Label class="px-3 text-xs">METHOD</Label>
        <Input class="rounded-sm w-full h-[40px] text-xl {saveError  ? 'text-red-700 font-bold' : ''}"
            bind:value={fileName}
            on:input={() => (saveError = false)}
            placeholder="File Name"
        />
    </div>
    <div class="flex flex-row justify-end items-start space-x-2 py-2">
        {#if saveError}
            <p class="text-red-700 font-bold">File Already Exists</p>
        {/if}
        <Button
            class="rounded-sm {saveError
                ? 'text-lg'
                : 'text-xl'} w-[120px] h-[30px] p-3"
            on:click={() => saveRun(fileName, saveError)}
        >
            {#if saveError}
                OVERWRITE
            {:else}
                SAVE
            {/if}
        </Button>
        <Dialog.Root bind:open={loadDialogOpen}>
            <Dialog.Trigger>
                <Button
                    on:click={getSaveFiles}
                    class="rounded-sm w-[110px] h-[30px] p-3 text-xl"
                    >LOAD</Button
                >
            </Dialog.Trigger>
            <Dialog.Content>
                <Dialog.Header>Load Run</Dialog.Header>

                <Table.Root class="">
                    <Table.Header>
                        <Table.Row>
                            <Table.Head>Name</Table.Head>
                            <Table.Head>Last Modified</Table.Head>
                        </Table.Row>
                    </Table.Header>
                    <Table.Body>
                        {#if saveFiles}
                            {#each saveFiles as file}
                                <Table.Row
                                    on:click={() =>
                                        (loadFile = file)}
                                    class="hover:{file == loadFile
                                        ? 'bg-sky-200 '
                                        : 'bg-sky-50'} cursor-pointer {file ==
                                    loadFile
                                        ? 'bg-sky-200 '
                                        : ''}"
                                >
                                    <Table.Cell
                                        >{file.name}</Table.Cell
                                    >
                                    <Table.Cell
                                        >{new Date(
                                            file.lastModified *
                                                1000,
                                        ).toLocaleString("en-GB", {
                                            day: "2-digit",
                                            month: "2-digit",
                                            year: "2-digit",
                                            hour: "2-digit",
                                            minute: "2-digit",
                                        })}</Table.Cell
                                    >
                                </Table.Row>
                            {/each}
                        {/if}
                    </Table.Body>
                </Table.Root>
                <Dialog.Footer>
                    <Dialog.Close>
                        <Button on:click={() => loadRun(loadFile)} 
                            >Load
                        </Button>
                        <Button
                            on:click={() =>
                                (loadDialogOpen = false)}
                            >Cancel</Button
                        >
                    </Dialog.Close>
                </Dialog.Footer>
            </Dialog.Content>
        </Dialog.Root>
        <Dialog.Root>
            <Dialog.Trigger>
                <Button
                    class="rounded-sm w-[110px] h-[30px] p-3 text-xl"
                    >NEW</Button
                >
            </Dialog.Trigger>
            <Dialog.Content>
                <Dialog.Header>New File Wizard</Dialog.Header>
                <Label>Name</Label>
                <Input type="text" bind:value={newName}></Input>

                <Label>Dispense Volume μL</Label>
                <Input type="number" bind:value={newVolume}></Input>

                <Dialog.Footer>
                    <Dialog.Close
                        ><Button
                            on:click={() => {
                                $run = runcard.resetRun(newVolume);
                                fileName = newName;
                            }}>New File</Button
                        ></Dialog.Close
                    >
                </Dialog.Footer>
            </Dialog.Content>
        </Dialog.Root>
    </div>
</div>