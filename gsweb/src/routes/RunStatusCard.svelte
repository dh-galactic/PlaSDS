<script lang="ts">
    import {Progress} from "$lib/components/ui/progress";
    import {runState} from "$lib/stores/settingsStore";

    function formatTime(seconds: number): string {
        seconds = Math.floor(seconds); // Handle floating numbers by flooring them
        const minutes = Math.floor(seconds / 60);
        const remainingSeconds = seconds % 60;
        return `${String(minutes).padStart(2, '0')}:${String(remainingSeconds).padStart(2, '0')}`;
    }

    function formatDuration(milliseconds: number): string {
        let seconds = Math.floor(milliseconds / 1000);
        const hours = Math.floor(seconds / 3600);
        seconds %= 3600;
        const minutes = Math.floor(seconds / 60);
        seconds %= 60;

        const formattedMinutes = String(minutes).padStart(2, '0');
        const formattedSeconds = String(seconds).padStart(2, '0');

        return hours > 0 
            ? `${hours}:${formattedMinutes}:${formattedSeconds}` 
            : `${formattedMinutes}:${formattedSeconds}`;
    }
</script>

{#if $runState.status!='Idle' }
<div class="w-full flex flex-row m-0 p-2">
            <div class="w-full p-2 text-xl text-center flex flex-col items-center">
                <div class="text-3xl pb-1"> Current Step: {$runState.currentStep} / {$runState.totalSteps}</div>
                <Progress class="w-4/5 text-xl text-white h-[40px]" value = {($runState.currentStep/$runState.totalSteps) *100} />
                <div class="flex flex-row w-3/5 justify-between"> 
                <div class="pl-5">Running for: {formatDuration(new Date().getTime() - new Date($runState.startTime).getTime() )}</div> 
                <div class="pr-5">
                Estimated Time Left: { formatDuration(((new Date().getTime() - new Date($runState.startTime).getTime()) /$runState.currentStep) * ($runState.totalSteps-$runState.currentStep) )}</div>
            </div>
        </div>
    </div>
{/if}
