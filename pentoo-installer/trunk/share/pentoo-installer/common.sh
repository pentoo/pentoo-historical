#!/bin/bash
# This script is released under the GNU General Public License 3.0
# Check the COPYING file included with this distribution

# to be sourced by other scripts

##############################
## START: define constants ##
readonly DESTDIR="/mnt/gentoo"
# This error code will be used when the user cancels a process
# dialog and Xdialog use 1 for cancel, Xdialog returns 255 upon closing of the box
readonly ERROR_CANCEL=64
readonly ISNUMBER='^[0-9]+$'
# use the first VT not dedicated to a running console
readonly LOG="/dev/tty8"
readonly TITLE="Pentoo Installation"
## END: define constants ##
############################

########################################
## START: initialize global variables ##
## END: initialize global variables ##
######################################

# source error handling/functions
# TODO: activate this once all code fullfills it
# source "${SHAREDIR}"/error.sh || exit $?

##############################
## START: utility functions ##

# get_dialog()
# prints used dialog programm: 'dialog' or 'Xdialog'
#
get_dialog() {
	# let's support Xdialog for the fun of it
	if [ ! $(type "Xdialog" &> /dev/null) ] && [ -v 'DISPLAY' ] && [ -n "${DISPLAY}" ]; then
		echo 'Xdialog'
	else
		echo 'dialog'
	fi
	return 0
}

# show_dialog()
# uses dialogSTDOUT
# an el-cheapo dialog wrapper
# parameters: see dialog(1) and Xdialog(1
# STDOUT and STDERR is switched compared to 'dialog' and 'Xdialog'
# usage: MYVAR="$(show_dialog .......)"
# returns:
# - 0 for Ok, result is written to STDOUT
# - 64 when user clicks cancel or closes the box
# - anything else is a real error
#
show_dialog() {
	# this script supports dialog and Xdialog but writes result to STDOUT
	# returns 64 if user cancels or closes the box!
	# detect auto-width and auto-height
	local _ARGUMENTS=
	local _HEIGHT=
	local _WIDTH=
	local _BOXOPTION_INDEX=
	local _INDEX=0
	local _WHICHDIALOG=
	local ANSWER=
	local _DIALOGRETURN=
	local _XDIALOG_AUTOSIZE_PERCENTAGE=33
	# copy array of arguments so we can write to it
	# also prepend our own arguments
	_ARGUMENTS=("$@") || return $?
	_ARGUMENTS=( '--backtitle' "${TITLE}" '--aspect' '15' "$@") || return $?
	# decide which dialog to use
	_WHICHDIALOG="$(get_dialog)"
	# for Xdialog: autosize does not work well with a title, use percentage of max-size
	if [ "${_WHICHDIALOG}" = 'Xdialog' ]; then
		# loop arguments and search for the box option
		# also swap --title and --backtitle
		while [ "${_INDEX}" -lt "${#_ARGUMENTS[@]}" ]; do
			case "${_ARGUMENTS[$_INDEX]}" in
				# all of these have the format: --<boxoption> text height width
				'--calendar' | '--checklist' | '--dselect' | '--editbox' | '--form' | '--fselect' | '--gauge' | '--infobox' | '--inputbox' | '--inputmenu' | '--menu' | '--mixedform' | '--mixedgauge' | '--msgbox' | '--passwordbox' | '--passwordform' | '--pause' | '--progressbox' | '--radiolist' | '--tailbox' | '--tailboxbg' | '--textbox' | '--timebox' | '--yesno')
					# prevent multiple box options
					[ -n "${_BOXOPTION_INDEX}" ] && return 1
					_BOXOPTION_INDEX="${_INDEX}"
					;;
				# swap title and backtitle for Xdialog
				'--title')
					_ARGUMENTS[${_INDEX}]='--backtitle'
					;;
				# swap title and backtitle for Xdialog
				'--backtitle')
					_ARGUMENTS[${_INDEX}]='--title'
					;;
				*) ;;
			esac
			_INDEX="$((_INDEX+1))" || return $?
		done
		# check if box option was found
		if [ -z "${_BOXOPTION_INDEX}" ]; then
			echo "ERROR: Cannot find box option. Exiting with an error!" 1>&2
			return 1
		fi
		if [ "$((${_BOXOPTION_INDEX}+3))" -ge "${#_ARGUMENTS[@]}" ]; then
			echo "ERROR: cannot find height and width for box option '"${_ARGUMENTS[${_BOXOPTION_INDEX}]}"'. Exiting with an error!" 1>&2
			return 1
		fi
		# only fix width/height for these box options
		case "${_ARGUMENTS[${_BOXOPTION_INDEX}]}" in
			'--menu' | '--gauge')
				_HEIGHT="${_ARGUMENTS[$((_BOXOPTION_INDEX+2))]}" || return $?
				_WIDTH="${_ARGUMENTS[$((_BOXOPTION_INDEX+3))]}" || return $?
				# check if width/height were found
				if [ -z "${_HEIGHT}" ] || [ -z "${_WIDTH}" ]; then
					echo "ERROR: Did not find box option with height/width. Exiting with an error" 1>&2
					return 1
				fi
				# use defined percentage of max-size
				if [ "${_HEIGHT}" -eq 0 ] && [ "${_WIDTH}" -eq 0 ]; then
					_HEIGHT=$("${_WHICHDIALOG}" --print-maxsize 2>&1 | tr -d ',' | cut -d ' ' -f2) || return $?
					_WIDTH=$("${_WHICHDIALOG}" --print-maxsize 2>&1 | tr -d ',' | cut -d ' ' -f3) || return $?
					_HEIGHT=$((${_HEIGHT} * ${_XDIALOG_AUTOSIZE_PERCENTAGE} / 100)) || return $?
					_WIDTH=$((${_WIDTH} * ${_XDIALOG_AUTOSIZE_PERCENTAGE} / 100)) || return $?
					# write new values to copy of arguments array
					_ARGUMENTS[$((_BOXOPTION_INDEX+2))]="${_HEIGHT}" || return $?
					_ARGUMENTS[$((_BOXOPTION_INDEX+3))]="${_WIDTH}" || return $?
				fi
				;;
			*) ;;
		esac
	fi
	# switch STDOUT and STDERR and execute 'dialog' or Xdialog'
	_ANSWER=$("${_WHICHDIALOG}" "${_ARGUMENTS[@]}" 3>&1 1>&2 2>&3)
	_DIALOGRETURN=$?
	# check if user clicked cancel or closed the box
	if [ "${_DIALOGRETURN}" -eq "1" ] || [ "${_DIALOGRETURN}" -eq "255" ]; then
		return ${ERROR_CANCEL}
	elif [ "${_DIALOGRETURN}" -ne "0" ]; then
		return "${_DIALOGRETURN}"
	fi
	# no error or cancel, echo to STDOUT
	echo -n "${_ANSWER}"
	return 0
}

# show_dialog_rsync()
# runs rsync, displays output as gauge dialog
# tee's log to "${LOG}"
# options to rsync should include '--progress' or the gauge will not move ;)
#
# parameters (required):
#  _OPTIONS: options for rsync
#  _SOURCE: source for rsync
#  _DESTINATION: destination for rsync
#  _MSG: message for gauge dialog
#
# returns $ERROR_CANCEL=64 on user cancel
# anything else is a real error
# reason: show_dialog() needs a way to exit "Cancel"
#
show_dialog_rsync() {
	# check input
	check_num_args "${FUNCNAME}" 4 $# || return $?
	local _OPTIONS="${1}"
	local _SOURCE="${2}"
	local _DESTINATION="${3}"
	local _MSG="${4}"
	rsync ${_OPTIONS} ${_SOURCE} ${_DESTINATION} 2>&1 \
		| tee "${LOG}" \
		| awk -f "${SHAREDIR}"/rsync.awk \
		| sed --unbuffered 's/\([0-9]*\).*/\1/' \
		| show_dialog --gauge "${_MSG}" 0 0
	_RET_SUB=$?
	if [ "${_RET_SUB}" -ne 0 ]; then
		show_dialog --msgbox "Failed to rsync '${_DESTINATION}'. See the log output for more information" 0 0
		return "${_RET_SUB}"
	fi
	return 0
}

## END: utility functions ##
############################
