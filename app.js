function toggleSidebar() {

    const sidebar =
        document.getElementById("sidebar");

    if (sidebar) {
        sidebar.classList.toggle("open");
    }
}


function filterTable() {

    const input =
        document.getElementById("globalSearch");

    if (!input) return;

    const query =
        input.value.toLowerCase();

    document
        .querySelectorAll("table.filterable tbody tr")
        .forEach(row => {

            const text =
                row.innerText.toLowerCase();

            row.style.display =
                text.includes(query)
                    ? ""
                    : "none";
        });
}


document.addEventListener(
    "DOMContentLoaded",
    function () {

        const form =
            document.getElementById("quizForm");

        if (!form) return;


        let seconds = 120;

        const timer =
            document.getElementById("timer");


        const interval =
            setInterval(function () {

                seconds--;

                const minutes =
                    String(
                        Math.floor(seconds / 60)
                    ).padStart(2, "0");

                const remaining =
                    String(
                        seconds % 60
                    ).padStart(2, "0");

                timer.textContent =
                    `${minutes}:${remaining}`;


                if (seconds <= 0) {

                    clearInterval(interval);

                    form.requestSubmit();
                }

            }, 1000);


        form.addEventListener(
            "submit",
            async function (event) {

                event.preventDefault();

                clearInterval(interval);


                const answers = [
                    0, 1, 2, 3
                ].map(function (index) {

                    return form.querySelector(
                        `[name="q${index}"]`
                    ).value;

                });


                const response =
                    await fetch(
                        "/api/aptitude",
                        {
                            method: "POST",

                            headers: {
                                "Content-Type":
                                    "application/json"
                            },

                            body: JSON.stringify({
                                answers: answers
                            })
                        }
                    );


                const data =
                    await response.json();


                const result =
                    document.getElementById(
                        "result"
                    );


                result.classList.remove(
                    "hidden"
                );


                result.innerHTML = `
                    <b>
                        Result:
                        ${data.score}/${data.total}
                    </b>
                    <br>
                    <small>
                        ${
                            data.score >= 3
                            ? "Excellent! Shortlist recommended."
                            : "Keep practicing and try again."
                        }
                    </small>
                `;


                form.querySelectorAll(
                    "input, button"
                ).forEach(function (element) {

                    element.disabled = true;

                });

            }
        );

    }
);