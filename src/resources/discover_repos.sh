#!/bin/sh

#DLPX_REPO_CFGFILE='ManualRepoDiscoveryFileNotProvided'
#${DELPHIX_DIR}/../../..
#DLPX_BIN_JQ=/u01/delphix/toolkit/Delphix_COMMON_56c4f1568fe9_a24eef3c6e13_14_host/scripts/jq/linux_x86/bin/jq
TOOLKIT_VERSION="0.0.6"
DLPX_TOOLKIT_NAME="mongo"
DLPX_LOG_DIRECTORY="/tmp"
TIMESTAMP=$(date +%Y-%m-%dT%H:%M:%S)
CONFIG_OUTPUT_FILE="delphix_${DLPX_TOOLKIT_NAME}_config.dat"
ERROR_LOG="${DLPX_LOG_DIRECTORY}/delphixpy_${DLPX_TOOLKIT_NAME}_error.log"
DEBUG_LOG="${DLPX_LOG_DIRECTORY}/delphixpy_${DLPX_TOOLKIT_NAME}_debug.log"

function log {
	Parms=$@
	TIMESTAMP=$(date +%Y-%m-%dT%H:%M:%S)
	die='no'
	if [[ $1 = '-d' ]]; then
		shift
		die='yes'
		Parms=$@
	fi
	#printf "[${TIMESTAMP}][DEBUG][%s][%s]:[$Parms]\n" $DLPX_TOOLKIT_WORKFLOW $PGM_NAME
	printf "[${TIMESTAMP}][DEBUG][%s][%s]:[$Parms]\n" $DLPX_TOOLKIT_WORKFLOW $PGM_NAME >> $DEBUG_LOG
	if [[ $die = 'yes' ]]; then
		exit 2
	fi
}
# Log error and write to the errorlog
function errorLog {
	TIMESTAMP=$(date +%Y-%m-%dT%H:%M:%S)
	log "$@"
	echo -e "[${TIMESTAMP}][ERROR][$@]" >>$ERROR_LOG
}
# Write to log and errorlog before exiting with an error code
function die {
	TIMESTAMP=$(date +%Y-%m-%dT%H:%M:%S)
	errorLog "$@"
	exit 2
}
# Function to check for errors and die with passed in error message
function errorCheck {
	if [ $? -ne 0 ]; then
		die "$@"
	fi
}
# Function to check for errors and die with passed in error message
function errorChecktReturn {
	if [ $? -ne 0 ]; then
		errorLog "$@"
		log "$@. Please check $DEBUG_LOG and $ERROR_LOG for more details."
		echo "\"$@\"" > $DLPX_OUTPUT_FILE
		if [ $# -eq 2 ]; then
			if [ $2 = "src_unfreeze_io" ]; then
				src_unfreeze_io
			elif [ $2 = "vdb_unfreeze_io" ]; then
				vdb_unfreeze_io
			fi
		fi
		exit 0
	fi
}
# Function to collect system info ARCH, OSTYPE, OSVERSION, MONGO_VERSION
function getSystemInfo {
	log "getSystemInfo: Getting system info"
	ARCH=$(uname -p)
	OSTYPE=$(uname)
	if [ "$OSTYPE" = "SunOS" ]; then
		OSTYPE="Solaris"
		OSVERSION=$(uname -v)
		OSSTR="$OSTYPE ${REV}(${ARCH} `uname -v`)"
	elif [ "$OSTYPE" = "AIX" ]; then
		OSSTR="$OSTYPE `oslevel` (`oslevel -r`)"
		OSVERSION=$(oslevel)
	elif [ "$OSTYPE" = "Linux" ]; then
		if [ -f /etc/redhat-release ]; then
			OSTYPE=RedHat
			OSVERSION=$(cat /etc/redhat-release | sed 's/.*release\ //' | sed 's/\ .*//')
		else
			die "Unsupported Linux Distro"
			OSTYPE=Unknown
			OSVERSION=Unsupported
		fi
	fi
	# Get Mongo version
	MONGO_VERSION=$($MONGO_INSTALL_PATH --version | grep "db version" | awk '{print $3}')
	MONGO_STORAGE_ENGINE=
}
# Confirm that JQ is available on this system and add it to path
function initializeJQ {
	# Add jq to PATH for convenience. Note that it is appended to the front so we
	# will always use it even if jq is installed elsewhere on the machine
	PATH="$(dirname "$DLPX_BIN_JQ"):${PATH}"
	# Confirm that invoking jq works properly
	jq '.' <<< '{}' >/dev/null 2>/dev/null
	errorCheck 'Unable to initialize JQ'
}
# Quotes strings for use with JSON. Fails if the number of arguments is not
# exactly one because it will not do what the user likely expects.
function jqQuote {
	if [[ "$#" -ne 1 ]]; then
		log -d "Wrong number of arguments to jqQuote: $@"
	fi
	$DLPX_BIN_JQ -R '.' <<< "$1"
}
function purgeLogs {
	#log "Checking Log File Sizes ... "
	# Once the log files exceed 20000 rows remove the first 20000 of them.
	lines=$(wc -l $DEBUG_LOG)
	if [[ $? -eq 0 ]]; then
		lines=$(echo $lines | awk '{print $1}')
		if [[ $lines -gt 20000 ]]; then
			if [ -f ${DEBUG_LOG}.9 ]; then
				mv ${DEBUG_LOG}.9 ${DEBUG_LOG}.10
			fi
			if [ -f ${DEBUG_LOG}.8 ]; then
				mv ${DEBUG_LOG}.8 ${DEBUG_LOG}.9
			fi
			if [ -f ${DEBUG_LOG}.7 ]; then
				mv ${DEBUG_LOG}.7 ${DEBUG_LOG}.8
			fi
			if [ -f ${DEBUG_LOG}.6 ]; then
				mv ${DEBUG_LOG}.6 ${DEBUG_LOG}.7
			fi
			if [ -f ${DEBUG_LOG}.5 ]; then
				mv ${DEBUG_LOG}.5 ${DEBUG_LOG}.6
			fi
			if [ -f ${DEBUG_LOG}.4 ]; then
				mv ${DEBUG_LOG}.4 ${DEBUG_LOG}.5
			fi
			if [ -f ${DEBUG_LOG}.3 ]; then
				mv ${DEBUG_LOG}.3 ${DEBUG_LOG}.4
			fi
			if [ -f ${DEBUG_LOG}.2 ]; then
				mv ${DEBUG_LOG}.2 ${DEBUG_LOG}.3
			fi
			if [ -f ${DEBUG_LOG}.1 ]; then
				mv ${DEBUG_LOG}.1 ${DEBUG_LOG}.2
			fi
			if [ -f ${DEBUG_LOG}.0 ]; then
				mv ${DEBUG_LOG}.0 ${DEBUG_LOG}.1
			fi
			cp $DEBUG_LOG ${DEBUG_LOG}.0
			cat /dev/null > $DEBUG_LOG
		fi
	fi
	lines=$(wc -l $ERROR_LOG)
	if [[ $? -eq 0 ]]; then
		lines=$(echo $lines | awk '{print $1}')
		if [[ $lines -gt 20000 ]]; then
		 if [ -f ${ERROR_LOG}.9 ]; then
			mv ${ERROR_LOG}.9 ${ERROR_LOG}.10
		 fi
		 if [ -f ${ERROR_LOG}.8 ]; then
			mv ${ERROR_LOG}.8 ${ERROR_LOG}.9
		 fi
		 if [ -f ${ERROR_LOG}.7 ]; then
			mv ${ERROR_LOG}.7 ${ERROR_LOG}.8
		 fi
		 if [ -f ${ERROR_LOG}.6 ]; then
			mv ${ERROR_LOG}.6 ${ERROR_LOG}.7
		 fi
		 if [ -f ${ERROR_LOG}.5 ]; then
			mv ${ERROR_LOG}.5 ${ERROR_LOG}.6
		 fi
		 if [ -f ${ERROR_LOG}.4 ]; then
			mv ${ERROR_LOG}.4 ${ERROR_LOG}.5
		 fi
		 if [ -f ${ERROR_LOG}.3 ]; then
			mv ${ERROR_LOG}.3 ${ERROR_LOG}.4
		 fi
		 if [ -f ${ERROR_LOG}.2 ]; then
			mv ${ERROR_LOG}.2 ${ERROR_LOG}.3
		 fi
		 if [ -f ${ERROR_LOG}.1 ]; then
			mv ${ERROR_LOG}.1 ${ERROR_LOG}.2
		 fi
		 if [ -f ${ERROR_LOG}.0 ]; then
			mv ${ERROR_LOG}.0 ${ERROR_LOG}.1
		 fi
		 cp $ERROR_LOG ${ERROR_LOG}.0
		 cat /dev/null > $ERROR_LOG
	  fi
   fi
}
# Keep for Library Verification ...
function hey {
   echo "there"
}
getVersion()
{
	VERSION=$($INSTALLPATH --version)
	if [ $? -ne 0 ]
	then
		log -d "Unable to run command \"$INSTALLPATH --version\" to capture the version of Mongo. Please check your Environment."
		errorLog "Unable to run command \"$INSTALLPATH --version\" to capture the version of Mongo. Please check your Environment."
	else
		VERSION=$(echo $VERSION  | grep "db version" | awk '{print $3}'	)
		log "VERSION=$VERSION"
	fi
}
assembleJson()
{
	# Assemble JSON and write output variables to output file
	CURRENT_REPO='{}'
	PRETTYNAME="PY EDSI MongoDB (${VERSION})"
	CURRENT_REPO=$(jq ".mongo_install_path = $(jqQuote "$INSTALLPATH")" <<< "$CURRENT_REPO")
	CURRENT_REPO=$(jq ".mongo_shell_path = $(jqQuote "$SHELLPATH")" <<< "$CURRENT_REPO")
	CURRENT_REPO=$(jq ".version = $(jqQuote "$VERSION")" <<< "$CURRENT_REPO")
	CURRENT_REPO=$(jq ".pretty_name = $(jqQuote "$PRETTYNAME")" <<< "$CURRENT_REPO")
	REPOSITORIES=$(jq ". + [$CURRENT_REPO]" <<< "$REPOSITORIES")
}

DLPX_TOOLKIT_WORKFLOW="repoDiscovery"
if [ -f $HOME/.setDelphixMongoEnv ]; then
    log "$HOME/.setDelphixMongoEnv exists"
    . $HOME/.setDelphixMongoEnv
else
    log "$HOME/.setDelphixMongoEnv does not exists"
fi

if [ -z "$MONGO_REPO_CFGFILE" ]; then
	if [ "${DLPX_TOOLKIT_WORKFLOW}" = "repoDiscovery" ]; then
		log "Env variable MONGO_REPO_CFGFILE not defined."
		log "MONGO_REPO_CFGFILE=$MONGO_REPO_CFGFILE"
		log "Manual/Custom repo Discovery disabled"
	fi
else
	if [ $DLPX_TOOLKIT_WORKFLOW = "repoDiscovery" ]; then
	    log "MONGO_REPO_CFGFILE=$MONGO_REPO_CFGFILE"
		log "Manual/Custom repo Discovery enabled"
	fi
fi

if [[ $DLPX_TOOLKIT_WORKFLOW != "repoDiscovery" &&  $DLPX_TOOLKIT_WORKFLOW != "status" ]]; then
	echo "============================================================================================================================================================"  >> $DEBUG_LOG
	echo "Workflow : $DLPX_TOOLKIT_WORKFLOW - $PGM_NAME" >> $DEBUG_LOG
	echo "============================================================================================================================================================"  >> $DEBUG_LOG
fi
log "Mongo Toolkit Version : $TOOLKIT_VERSION"
PGM_NAME="repoDiscovery.sh"             # used in log and errorLog
log "Executing $PGM_NAME"
log "------------------------------------------------------- "
initializeJQ
installPathFound=0
shellPathFound=0
i=0
e1=0
e2=0
e3=0
REPOSITORIES='[]'
# See if mongo service exist
#FIND_BIN_PATH=/m01/app/mongo/product/mongodb #Dell
DLPX_REPO_CFGFILE=$MONGO_REPO_CFGFILE
MANUAL_MONGO_FIND=0
MANUAL_MONGO_FIND_FILE=$DLPX_REPO_CFGFILE
#MANUAL_MONGO_FIND_FILE=/tmp/MONGO_INSTALL_PATH.txt
log "MANUAL_MONGO_FIND_FILE=$MANUAL_MONGO_FIND_FILE"
if [ -r $MANUAL_MONGO_FIND_FILE ]
then
	MANUAL_MONGO_FIND=1
	log "Manual/Custom Discovery Enabled"
else
	MANUAL_MONGO_FIND=0
	log "AutoDiscovery Enabled. Using default path for mongo /usr/bin/mongod"
fi
if [ $MANUAL_MONGO_FIND -eq 1 ]; then
	#cat $MANUAL_MONGO_FIND_FILE|awk -F"=" '{ print $2}'| while read line
	while read line
	do
		if [[ ${line} = *"MONGO_PATH"* ]]; then
			FIND_BIN_PATH=`echo $line|awk -F"=" '{ print $2}'`
			log "Manual Discovery Path Provided : $FIND_BIN_PATH"
			FIND_BIN_PATH=$(dirname $FIND_BIN_PATH)
			log "FIND_BIN_PATH : $FIND_BIN_PATH"
			if [ -d $FIND_BIN_PATH ]; then
				INSTALLPATH=$(find $FIND_BIN_PATH -name mongod 2>&1 | head -1)
				if [[ ${INSTALLPATH} = *"Permission denied"* ]]; then
					e1=1
					log "Insufficient privileges to scan $FIND_BIN_PATH"
				elif [[ "$INSTALLPATH" = '' ]]; then
					e2=1
					# Install path not found - return empty repo config
					log "Install path $FIND_BIN_PATH/*..*/mongod not found"
				else
					installPathFound=1
					log "INSTALLPATH=$INSTALLPATH"
				fi

				# See if mongo shell exist
				SHELLPATH=$(find $FIND_BIN_PATH -name mongo | head -1)
				if [[ "$SHELLPATH" = '' ]]; then
					e3=1
					# Shell path not found - return empty repo config
					log "Shell path $FIND_BIN_PATH/*..*/mongo not found"
				else
					shellPathFound=1
					log "SHELLPATH=$SHELLPATH"
				fi

				getVersion
				if [ $installPathFound -eq 1 ] && [ $shellPathFound -eq 1 ]; then
					log "Mongo Installations found"
					assembleJson
					i=$(( $i + 1))
				fi
			else
				log "Invalid Path : $line OR Incorrect permissions to access it."
			fi
		fi
	done < 	$MANUAL_MONGO_FIND_FILE
	log "Number of Installations found : $i"
	if [ $i -eq 0 ]; then
		echo "[]"
		exit 0
	fi
else
	log "Auto Discovery"
	FIND_BIN_PATH=/usr/bin
	log "FIND_BIN_PATH : $FIND_BIN_PATH"
	INSTALLPATH=$(find $FIND_BIN_PATH -name mongod 2>&1 | head -1)
	if [[ ${INSTALLPATH} = *"Permission denied"* ]]; then
		log "Insufficient privileges to scan $FIND_BIN_PATH"
		echo "[]"
		exit 0
	elif [[ "$INSTALLPATH" = '' ]]; then
		# Install path not found - return empty repo config
		log "Install path $FIND_BIN_PATH/*..*/mongod not found"
		echo "[]"
		exit 0
	fi
	log "INSTALLPATH=$INSTALLPATH"
	# See if mongo shell exist
	SHELLPATH=$(find $FIND_BIN_PATH -name mongo | head -1)
	if [[ "$SHELLPATH" = '' ]]; then
		# Shell path not found - return empty repo config
		log "Shell path $FIND_BIN_PATH/*..*/mongo not found"
		echo "[]"
		exit 0
	fi
	log "SHELLPATH=$SHELLPATH"

	getVersion
	assembleJson
fi
echo "$REPOSITORIES"
echo "`echo $REPOSITORIES|python -m json.tool`" >> $DEBUG_LOG
exit 0
