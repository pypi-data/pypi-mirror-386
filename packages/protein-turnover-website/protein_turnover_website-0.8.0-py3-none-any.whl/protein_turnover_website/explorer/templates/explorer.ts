type URLStr = string

type Key = "mzml" | "pepxml" | "protxml"

type ExplorerClass = Readonly<{
    change_directory_url: URLStr
    selector: string
    key: Key // what we are selecting
    multi: boolean
}>
type State = {
    parent: string
    mountpoint: string
    sorton: string
    ascending: boolean
    name?: string
}
type SelectedClass = Readonly<{
    selected: string[]
    state: State
    key: Key
}>
function explorer(config: ExplorerClass) {
    const $explorer = $(config.selector)

    let isMouseDown = false
    let multi = config.multi
    let key = config.key

    $(document).on("mouseup", multi_mouseup) // catch all for mouseup

    $explorer
        .on("mousedown", "table > tbody > tr.file", multi_mousedown)
        .on("mouseover", "table > tbody > tr.file", multi_mouseover)
        .on("click", "table > tbody > tr.file", select_single)
        .on("dblclick", "table > tbody > tr.file", select_dblclick)
        // change mountpoint
        .on("click", "[data-mountpoint]", change_mountpoint)
        // change directory
        .on("dblclick", "table > tbody > tr.dir", select_directory)
        // sorting
        .on("click", "table > thead > tr > th > div", sorton)
        .on("click", "a[data-state]", breadcrumb)

    return { change_directory: change_directory, multi_select: multi_select }

    // functions only
    function multi_mousedown(e: JQuery.MouseDownEvent) {
        if (!multi) {
            return
        }
        e.preventDefault()
        isMouseDown = true
        $(e.currentTarget).toggleClass("selected")
        trigger_selected(get_current_state())
        //return false;
    }

    function multi_mouseover(e: JQuery.MouseOverEvent) {
        if (!multi) {
            return
        }
        e.preventDefault()
        if (isMouseDown) {
            $(e.currentTarget).toggleClass("selected")
            trigger_selected(get_current_state())
        }
    }

    function multi_mouseup() {
        isMouseDown = false
    }

    function select_single(e: JQuery.ClickEvent | JQuery.DoubleClickEvent) {
        isMouseDown = false
        if (multi) {
            return
        }
        $(e.currentTarget).siblings(".selected").removeClass("selected")
        $(e.currentTarget).addClass("selected")
        trigger_selected(get_current_state())
    }
    function select_dblclick(e: JQuery.DoubleClickEvent) {
        select_single(e)
        if (multi) return
        $explorer.trigger("doubleclick.to")
    }

    function change_mountpoint(e: JQuery.ClickEvent) {
        e.preventDefault()
        const href = $(e.currentTarget).attr("href") as string
        let state = get_current_state()
        // we already have ?mountpoint= in href
        // @ts-ignore
        delete state.mountpoint
        state.parent = "." // change to top level of new mountpoint
        $.get(href, state)
            .then((html) => $explorer.html(html))
            .then(() => trigger_selected(get_current_state()))
            .fail(function () {
                toastr.error("can't change mountpoints!")
            })
    }

    function select_directory(e: JQuery.DoubleClickEvent) {
        // e.preventDefault()
        const name = $(e.currentTarget).data().name
        const state = get_current_state()

        state.name = name
        to_directory(state)
    }

    function breadcrumb(e: JQuery.ClickEvent) {
        e.preventDefault()
        const state = get_selected($(e.currentTarget)).state

        to_directory(state)
    }

    function to_directory(state: State): JQuery.Promise<any> {
        return change_directory(state)
            .then(() => trigger_selected(state))
            .fail(function () {
                toastr.error("can't change directories!")
            })
    }

    function sorton(e: JQuery.ClickEvent) {
        const sorton = $(e.currentTarget).data().sorton
        const state = get_current_state()
        if (state.sorton === sorton) {
            state.ascending = !state.ascending
        }
        state.sorton = sorton
        change_directory(state)
            .then(() => trigger_selected(state))
            .fail(function () {
                toastr.error("can't change sort!")
            })
    }

    function get_current_state(): State {
        return get_selected($explorer.find("table")).state
    }

    function find_selected(): JQuery {
        return $explorer.find("table > tbody > tr.file.selected")
    }

    function trigger_selected(state: State): string[] {
        const s = find_selected()
            .map(function () {
                return this.dataset.name
            })
            .get()
        $explorer.trigger("selected.to", { selected: s, state: state, key: key } as SelectedClass)
        return s
    }

    function unselect() {
        find_selected().removeClass("selected")
    }

    function change_directory(state: State): JQuery.Promise<any> {
        return $.get(config.change_directory_url, state).then((html) => $explorer.html(html))
        // don't show fail! let caller do that
        // .fail(function () {
        //     toastr.error("failed to change directory!")
        // })
    }

    // pass in new state return old state
    function multi_select(newkey: Key, newmulti: boolean): [Key, boolean] {
        const old: [Key, boolean] = [key, multi]
        multi = newmulti
        key = newkey
        unselect()
        return old
    }

    function get_selected($target: JQuery<HTMLElement>): SelectedClass {
        return $target.data() as SelectedClass
    }
}
