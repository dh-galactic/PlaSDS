import { controllerIP } from "./stores/settingsStore";

export function controllerCommand(command: string, data: Object = {}) {
    let ipCall:any;

    controllerIP.subscribe((value) => (ipCall = value))
    let ip = "http://" + ipCall + ":8080/";
    return fetch(ip + "controller", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ command: command, data: data }),
    })
        .then((response) => {
            return response.json();
        })
        .catch((error) => {            
            console.error("Error", error);
        });
} 


