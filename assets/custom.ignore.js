// Ensures that only the 'deferred' script gets run - prevents calling the custom .js file twice
// Ignore the first error output on console
if (renderer) { 
    // Function that takes care of the scrolling position of the console output
    consoleOut() 

    // Function that clears the console when the clear console button is pressed
    // consoleClear()

    // Function that refreshes the page while making sure that the chronos process is terminated
    refreshPage()

    // Function that allows the "enter" keypress/send command press to be used to send commands 
    commandEnter()

    // Function that refreshes the video-streamer iframe and plays the video player when Chronos starts
    streamerRefresh()

    // Function that refreshes the video-streamer iframe when Chronos stops
    streamerRefresh2()
}

function consoleOut() {
    const iframe = document.getElementById('console-out');
    const iframeWindow = iframe.contentWindow;
    var iframeMaxScroll = 0
    var oldIframeHeight = 0;
    var top = 1000, left = 0;

    // Called upon each reload of the console window
    iframe.onload = function () { 
        
        iframeMaxScroll = iframeWindow.document.documentElement.scrollHeight; // Get's the iframe's max scroll height
        iframeWindow.addEventListener("scroll", function(e) {
            top = this.scrollY;
            left = this.scrollX;
            }
        )
        // console.log(top);
        // console.log(top - (oldIframeHeight-200));
        // console.log(0.001*top);
        // Keeps the scroll at the bottom if its already at the bottom, otherwise allows the user to navigate freely 
        if ((top - (oldIframeHeight - 200) < 0.01*top) && (top - (oldIframeHeight - 200) > -0.01*top)) { // 200 ish is the magic number...need to fix this to be more general
            iframeWindow.scrollTo(left, iframeMaxScroll);
        } else {
            iframeWindow.scrollTo(left, top);
        }
        oldIframeHeight = iframeMaxScroll;
    }
}

// Don't think this is needed anymore, my callback function in the python script clears the console anyways
function consoleClear() {
    const clearButton = document.getElementById('button-5');

    clearButton.onclick = function() {
        var iframe = document.getElementById('console-out');
    }
}

function refreshPage() {
    const refreshButton = document.getElementById('button-refresh')
    window.onbeforeunload = function () {
        refreshButton.click()
    }
}

function commandEnter() {
    // Get the input field
    var input = document.getElementById("command-line-input");
    const sendCommandButton = document.getElementById('button-3');
    const startButton = document.getElementById('button-2');
    const stopButton = document.getElementById('button-4');
    const clearButton = document.getElementById('button-5');

    // Execute a function when the user presses a key on the keyboard
    input.addEventListener("keypress", function(event) {

        // If the user presses the "Enter" key on the keyboard
        if (event.key === "Enter") {
            // var chars = input.value.split(' ');

            // Commands for starting/stopping chronos + clearing the console output
            if (input.value == "start") {
                startButton.click()

            } else if (input.value == "stop") {
                stopButton.click()

            } else if (input.value == "clear") {
                clearButton.click()

            } else {
                // Send command
                sendCommandButton.click();
                // if (chars[0] == "create") {
                //     const msg = `Agent with id ${chars[2]} from agent group ${chars[1]} has been created!`
                //     document.getElementById('console-out').srcdoc += msg
                //     console.log(document.getElementById('console-out').srcdoc)
                // }
            }   
            sendCommandButton.click()
        }}
    )
    
    // sendCommandButton.onclick = function () {

    //     if (input.value == "start") {
    //         startButton.click()
    //     }

    //     if (input.value == "stop") {
    //         stopButton.click()
    //     }
        
    //     if (input.value == "clear") {
    //         clearButton.click()
    //     }
    // }
}

function streamerRefresh () {
    let p = document.getElementById('streamer-text')
    var config = {attributes: true, childList: true, subtree: true };

    // Looks out for change in hidden 'p' element, which changes when the .m3u8 file is read
    var observer = new MutationObserver(() => {
        if (p.innerHTML == 'a') {
            const iframe = document.getElementById('video-streamer');
            iframe.contentWindow.location.reload()
            iframe.onload = function () {
                iframe.contentWindow.document.getElementById('player').play();
            }
        }
    });

    observer.observe(p, config);
}

function streamerRefresh2 () {
    const stopButton = document.getElementById('button-4');
    const startButton = document.getElementById('button-2');
    const iframe = document.getElementById('video-streamer');
    stopButton.onclick = function () {
        iframe.contentWindow.document.getElementById('player').pause();
    }
    // startButton.onclick = function () {
    //     iframe.contentWindow.location.reload()
    //     // setTimeout(function() {
    //     //     iframe.contentWindow.location.reload()
    //     // }, 3000);
    // }
}