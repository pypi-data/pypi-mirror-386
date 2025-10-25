# A sentinel at the start of each record. The sentinel allows correct detection of variable
# number of fields produced by 'changes' and correct detection of patch presence and patch
# end. It thus must not be any of these charactes:
#   ':', since this is how a whatchanged (raw diff) entry starts;
#   'd', since this is how the patch starts ("diff");
#   '\n', since this is sometimes inserted by git before ':' and before 'diff';
#   '+', '-', ' ', '\\', since this is how a diff line starts,
#   'r', 'n', 'd', 'B', since this is how a diff may end ('rename', 'new file',
#       'deleted file', 'Binary files').
_SENTINEL = '#'
