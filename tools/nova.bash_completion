_nova_opts="" # lazy init
_nova_flags="" # lazy init
_nova_opts_exp="" # lazy init
_nova()
{
	local cur prev nbc cflags
	COMPREPLY=()
	cur="${COMP_WORDS[COMP_CWORD]}"
	prev="${COMP_WORDS[COMP_CWORD-1]}"

	if [ "x$_nova_opts" == "x" ] ; then
		nbc="`nova bash-completion | sed -e "s/  *-h  */ /" -e "s/  *-i  */ /"`"
		_nova_opts="`echo "$nbc" | sed -e "s/--[a-z0-9_-]*//g" -e "s/  */ /g"`"
		_nova_flags="`echo " $nbc" | sed -e "s/ [^-][^-][a-z0-9_-]*//g" -e "s/  */ /g"`"
		_nova_opts_exp="`echo "$_nova_opts" | tr ' ' '|'`"
	fi

	if [[ " ${COMP_WORDS[@]} " =~ " "($_nova_opts_exp)" " && "$prev" != "help" ]] ; then
		COMPLETION_CACHE=~/.novaclient/*/*-cache
		cflags="$_nova_flags "$(cat $COMPLETION_CACHE 2> /dev/null | tr '\n' ' ')
		COMPREPLY=($(compgen -W "${cflags}" -- ${cur}))
	else
		COMPREPLY=($(compgen -W "${_nova_opts}" -- ${cur}))
	fi
	return 0
}
complete -F _nova nova
