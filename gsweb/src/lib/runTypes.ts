    
export type RackType = {
    col: number,
    row: number,
    description: string
}
export type AutoSamplerPosition ={
    rack: number;
    position: number;
};

export type CommandBlock ={
    startPosition: number;
    endPosition: number;
    volume: number;
    waitSeconds: number;
};

export type ConnectionStatus = {
    hamilton: string;
    autosampler: string;
};

export type RunState = {
    status: string;
    currentStep: number;
    totalSteps: number;
    startTime: Date;
}


export type RunSettings = {
	probeDepth: number;
	speed: number;
	syringeSize: number;
    numRacks: number;
    rackType: RackType;
    flushAfter: number;
};

export type RunData = {
    fileName: string;
    settings: RunSettings;
    runState: RunState;
    run: CommandBlock[][];
}

export type RunError = {
    error:boolean
    type:string;
    description:string;
}