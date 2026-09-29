(function () {

    let eventSource = null;


    // ============================================================
    // Connect to FastAPI SSE
    // ============================================================

    function connectSSE(interviewId) {

        if (!interviewId) {

            console.error(
                "Cannot connect SSE: interview_id is missing."
            );

            return;
        }


        console.log(
            "Connecting SSE for:",
            interviewId
        );


        // Close an existing connection
        if (eventSource) {

            eventSource.close();
            eventSource = null;
        }


        const url =
            `http://localhost:8000/events/${encodeURIComponent(interviewId)}`;


        eventSource =
            new EventSource(url);


        // ========================================================
        // JOB COMPLETED
        // ========================================================

        eventSource.addEventListener(
            "job.completed",
            function (event) {

                console.log(
                    "Job completed:",
                    event.data
                );


                const data =
                    JSON.parse(event.data);


                /*
                 * Do NOT call /resume here.
                 *
                 * Just notify the Chainlit/browser layer
                 * that the background job is complete.
                 */

                window.dispatchEvent(
                    new CustomEvent(
                        "aget-job-completed",
                        {
                            detail: data
                        }
                    )
                );
            }
        );


        // ========================================================
        // JOB FAILED
        // ========================================================

        eventSource.addEventListener(
            "job.failed",
            function (event) {

                console.log(
                    "Job failed:",
                    event.data
                );


                const data =
                    JSON.parse(event.data);


                window.dispatchEvent(
                    new CustomEvent(
                        "aget-job-failed",
                        {
                            detail: data
                        }
                    )
                );
            }
        );


        // ========================================================
        // SSE ERROR
        // ========================================================

        eventSource.onerror =
            function (error) {

                console.error(
                    "SSE connection error:",
                    error
                );
            };
    }


    // ============================================================
    // Called when Chainlit wants SSE connection established
    // ============================================================

    window.addEventListener(
        "aget-connect-sse",
        function (event) {

            const interviewId =
                event.detail.interview_id;


            connectSSE(
                interviewId
            );
        }
    );


    // ============================================================
    // Expose function so the Chainlit frontend can start SSE
    // ============================================================

    window.agetConnectSSE =
        function (interviewId) {

            connectSSE(
                interviewId
            );
        };


})();