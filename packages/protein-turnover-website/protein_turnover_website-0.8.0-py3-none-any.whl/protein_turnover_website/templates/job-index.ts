type JobIndexClass = Readonly<{
    job_index_url: URLStr
    find_metadata_url: URLStr
    find_log_url: URLStr
    kill_job_url: URLStr
    restart_job_url: URLStr
    remove_job_url: URLStr
    refresh_jobs_url: URLStr

    refresh_delay: number
    queue_length: number
}>

type JsonReply = Readonly<{
    status: "OK" | "failed"
    msg: string
}>

type Refresh = Readonly<{
    running: string
    queued: string
    finished: string
}>

declare const JobIndex: JobIndexClass

jQuery(function ($) {
    const $tables = $(".jobs-table")
    const $running = $("#jobs-finished")
    const $refresh = $("#refresh")
    const dom = `<'row'<'col-12'i>>
    <'row'<'col-12'p>>
    <'row'<'col-sm-12 col-md-6'l><'col-sm-12 col-md-6'f>>
    <'row'<'col-sm-12'tr>>`
    const idmap = {
        "jobs-running": "running",
        "jobs-finished": "finished",
        "jobs-queued": "queued"
    }
    var dt: DataTables.Api | null = null // data table

    $tables.on("click", "tr[data-id] button[data-view]", function (e) {
        const $tr = $(e.currentTarget).parents("[data-id]")
        const $view = $tr.next("[data-metadata]")
        if ($view.length > 0) {
            $view
                .find(">:first-child >:first-child")
                .animate({ height: 0 }, 500, () => $view.remove())
            return
        }
        const dataid = $tr.data().id

        $.get(JobIndex.find_metadata_url, { dataid })
            .then((html) => {
                $(html).insertAfter($tr)
            })
            .fail(server_down)
    })

    $tables.on("click", "tr[data-id] button[data-log]", function (e) {
        const $button = $(e.currentTarget)
        const $tr = $button.parents("[data-id]")
        const $view = $tr.next("[data-metadata]")

        const dataid = $tr.data().id

        $button.html('<i class="fas fa-sync"></i>')
        $.get(JobIndex.find_log_url, { dataid })
            .then((html) => {
                if ($view.length > 0) {
                    $view.remove()
                }
                $(html).insertAfter($tr)
            })
            .fail(server_down)
    })
    $tables.on("click", "tr[data-metadata] button[data-closeme]", function (e) {
        const $view = $(this).parents("tr")
        $view.prev().find("button[data-log]").text("Logs")
        $view.find(">:first-child >:first-child").animate({ height: 0 }, 500, () => $view.remove())
    })

    $refresh.on("click", function () {
        $.get(JobIndex.refresh_jobs_url)
            .then((json: Refresh) => {
                dt?.destroy()

                $tables.each(function () {
                    const jobid = this.id as "jobs-running" | "jobs-queued" | "jobs-finished"
                    const which = idmap[jobid] as "running" | "queued" | "finished"
                    $(this).empty().html(json[which])
                })
                create_datatable()
            })
            .fail(server_down)
    })

    create_datatable()
    arm("button[data-kill]", JobIndex.kill_job_url)
    arm("button[data-restart]", JobIndex.restart_job_url)
    arm("button[data-remove]", JobIndex.remove_job_url)

    function create_datatable() {
        dt = $running.find("table").DataTable({ dom: dom, pageLength: JobIndex.queue_length })
    }
    function arm(delegate: string, url: string) {
        $tables.on("click", "tr[data-id] " + delegate, function (e) {
            const $tr = $(e.currentTarget).parents("[data-id]")
            const dataid = $tr.data().id

            $.get(url, { dataid })
                .then((json: JsonReply) => {
                    toastr.info(json.msg)
                    if (json.status === "OK") {
                        setTimeout(() => {
                            window.location.href = JobIndex.job_index_url
                        }, JobIndex.refresh_delay || 1000)
                    }
                })
                .fail(server_down)
        })
    }

    function server_down() {
        toastr.error("server down?", "Network Error", {
            closeButton: true,
            timeOut: 0,
            showDuration: 0,
            extendedTimeOut: 0
        })
    }
})
