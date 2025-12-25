# real_time_auction
real time auction platform using python it database locking. 


    <script>
        const roomName = "{{ room_name }}";
        const logDiv = document.querySelector('#log');
        const timerSpan = document.getElementById('timer');
        const priceSpan = document.querySelector('#price');
        const statusMsg = document.querySelector('status-msg');

        let endTime = new Date("{{ item.end_time|date:'c' }}").getTime();
        //const timerSpan = document.getElementById('timer');
        const bidBtn = document.querySelector('button');
        const bidInput = document.getElementById('bid-amount');

        const chatInput = document.querySelector('#chat-input');
        const chatSumbit = document.querySelector('#chat-submit');  


        const chatSocket = new WebSocket(
            'ws://' + window.location.host + '/ws/auction/' + roomName + '/'
        );

        chatSocket.onmessage = function(e) {
            const data = JSON.parse(e.data);
            console.log("Data:", data);

            //document.querySelector('#price').innerText = data.new_price;
            priceSpan.innerText = data.new_price;

            if (data.new_end_time) {
                endTime = new Date(data.new_end_time).getTime();

                const timerSpan = document.getElementById('timer');
                timerSpan.style.color = "orange";
                setTimeout(() => {timerSpan.style.color = "red"}, 1000);

                document.querySelector('button').disabled = false;
                document.getElementById('bid-amount').disabled = false;
                document.querySelector('button').innerText = "Place Bid";
            }
           
            //const log = document.querySelector('#log');
            //log.innerHTML += '<div>' + data.message + '<div>';
            
            if (data.type === 'chat') {
                const msgDiv = document.createElement('div');
                msgDiv.innerHTML = `<strong><span style="color: blue;">${data.username}:</span></strong> ${data.message}`;
                document.querySelector('#log').prepend(msgDiv);
                return;
            }

            if (data.type === 'status_update') {
                const msgDiv = document.createElement('div');

                msgDiv.style.color = 'gray';
                msgDiv.style.fontStyle = 'italic';
                msgDiv.style.fontSize = '0.9em';

                if (data.status === 'joined') {
                    msgDiv.innerText = `👋 ${data.username} joined the room.`;
                } else {
                    msgDiv.innerText = `🫷 ${data.username} left the room.`;
                }

                document.querySelector('#log').prepend(msgDiv);
                return;
                }
                       
            if (data.message) {
                const msgDiv = document.createElement('div');
                const timeStr = new Date().toLocaleTimeString();
                msgDiv.innerText = `[${timeStr}] ${data.message}`;

                const logBox = document.querySelector('#log');
                if (logBox) {
                    logBox.prepend(msgDiv);
                } else {
                    console.error("Could not find <div id='log'>");
                }
            }           
        };

        if (chatInput && chatSumbit) {
            chatSubmit.onclick = function(e) {
                const message = chatInput.value;
                if (message) {
                    chatSocket.send(JSON.stringify({
                        'type': 'chat_message',
                        'message': message
                    }));
                    chatInput.value = '';
                }
            };

            chatInput.onkeyup = function(e) {
                if (e.keyCode === 13) {
                    chatSubmit.click();
                }
            };
        } else {
            console.error("Error: Could not find <input id='chat-input'> or <button id='chat-submit'>");
        }

        
        
       
        function updateTimer() {
            const now = new Date().getTime();
            const distance = endTime - now;

            if (distance < 0) {
                clearInterval(timerInterval);
                timerSpan.innerText = "EXPIRED";
                timerSpan.style.color = "gray";
                bidBtn.disabled = true;
                bidInput.disabled = true;
                bidBtn.innerText = "Auction closed";
                return;
            }

            const minutes = Math.floor((distance % (1000 * 60 * 60)) / (1000 * 60));
            const seconds = Math.floor((distance % (1000 * 60 )) / 1000);
            timerSpan.innerText = minutes + "m " + seconds + "s ";
        }

        const timerInterval = setInterval(updateTimer, 1000);
        updateTimer();

        function submitBid() {
            const amountInput = document.getElementById('bid-amount');
            const amount = amountInput.value;

            const csrfInput = document.querySelector('[name=csrfmiddlewaretoken]');
            const csrftoken = csrfInput ? csrfInput.value : '';

            if (!csrftoken) {
                statusMsg.innerText = "Error: CSRF TOKEN MISSING. check template.";
                statusMsg.className = "error";
                return;
            }

            const statusMsg = document.getElementById('status-msg');

            fetch(`/auction/api/bid/${roomName}/`, {
                method: 'POST',
                headers: {
                    'Content-Type': 'application/json',
                    'X-CSRFToken' : csrftoken
                },
                body: JSON.stringify({ 'amount': amount})
            })
            .then(async response => {
                const contentType = response.headers.get("content-type");
                if (!contentType || !contentType.includes("application/json")) {
                    const text = await response.text();
                    throw new Error("Server returned non-JSON error (Check Terminal): " + response.status);
                }

                const data = await response.json();

                if (!response.ok) {
                    throw data;
                } 
                return data;
            })
            .then(data => {
                statusMsg.innerText = "Bid placed successfully";
                statusMsg.className = "success";
            })
            .catch(error => {
                console.error('Error:', error);
                //Display the actual error message
                statusMsg.innerText = error.message || error.error || "Something went wrong";
                statusMsg.className = "error";
            });
        }   
        
        chatSocket.onclose = function(e) {
            console.error('Chat socket closed unexpectedly');
        }; 

    </script>