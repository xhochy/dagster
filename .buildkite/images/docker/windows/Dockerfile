# escape=`

####################################################################################################
#
# DAGSTER BASE IMAGE
#
# We use this image to derive both an image for our Buildkite CI/CD pipeline, as well as a public
# Dagster image.
#
####################################################################################################
FROM mcr.microsoft.com/windows/servercore:ltsc2016 AS dagster-base-image

ARG PYTHON_VERSION
ARG PYTHON_MAJOR_VERSION

SHELL ["powershell", "-Command", "$ErrorActionPreference = 'Stop'; $ProgressPreference = 'SilentlyContinue';"]

ENV PYTHON_VERSION ${PYTHON_VERSION}
ENV PYTHON_MAJOR_VERSION ${PYTHON_MAJOR_VERSION}

RUN Write-Host ('Building integration image for Python {0}' -f $env:PYTHON_VERSION)
RUN certutil -generateSSTFromWU roots.sst ; `
    certutil -addstore -f root roots.sst ; `
    del roots.sst;

RUN $pythonUrl = ('https://www.python.org/ftp/python/{0}/python-{1}-amd64.exe' -f $env:PYTHON_VERSION, $env:PYTHON_VERSION); `
	Write-Host ('Downloading {0} ...' -f $pythonUrl); `
	[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; `
	try { `
		$pythonInstaller = 'python.exe'; `
		Invoke-WebRequest -Uri $pythonUrl -OutFile $pythonInstaller; `
		$hasExe = $true;  `
	} catch { `
		$pythonUrl = ('https://www.python.org/ftp/python/{0}/python-{1}.amd64.msi' -f $env:PYTHON_VERSION, $env:PYTHON_VERSION); `
		$pythonInstaller = 'python.msi'; `
		Write-Host ('Download failed, trying {0} ...' -f $pythonUrl); `
		Invoke-WebRequest -Uri $pythonUrl -OutFile $pythonInstaller; `
		$hasExe = $false `
	} `
	Write-Host 'Installing ...'; `
	if ($hasExe) { `
		Start-Process python.exe -Wait `
			-ArgumentList @( `
				'/quiet', `
				'InstallAllUsers=1', `
				'TargetDir=C:\Python', `
				'PrependPath=1', `
				'Shortcuts=0', `
				'Include_doc=0', `
				'Include_pip=0', `
				'Include_test=0' `
			); `
	} else { `
		Start-Process msiexec.exe -Wait `
			-ArgumentList @( `
				'/I python.msi', `
				'/quiet', `
				'/norestart', `
				'/passive', `
				'ADDLOCAL=ALL' `
			); `
	} `
    # the installer updated PATH, so we should refresh our local value
	$env:PATH = [Environment]::GetEnvironmentVariable('PATH', [EnvironmentVariableTarget]::Machine); `
	Write-Host 'Verifying install ...'; `
	Write-Host '  python --version'; python --version; `
	Write-Host 'Removing ...'; `
	Remove-Item $pythonInstaller -Force; `
	Write-Host 'Complete.'

# if this is called "PIP_VERSION", pip explodes with "ValueError: invalid truth value '<VERSION>'"
ENV PYTHON_PIP_VERSION 19.3.1

RUN $pipUrl = ('https://github.com/pypa/get-pip/raw/ffe826207a010164265d9cc807978e3604d18ca0/get-pip.py'); `
    $pipSHA256 = ('b86f36cc4345ae87bfd4f10ef6b2dbfa7a872fbff70608a1e43944d283fd0eee'); `
    Write-Host ('Downloading {0} ...' -f $pipUrl); `
	[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; `
	Invoke-WebRequest -Uri $pipUrl -OutFile 'get-pip.py'; `
	Write-Host ('Verifying download ...'); `
	if ((Get-FileHash 'get-pip.py' -Algorithm sha256).Hash -ne $pipSHA256) { `
		Write-Host 'FAILED!'; `
		exit 1; `
	}; `
	Write-Host ('Installing ...'); `
	python get-pip.py `
		--disable-pip-version-check `
		--no-cache-dir `
		('pip=={0}' -f $env:PYTHON_PIP_VERSION) `
	; `
	Remove-Item get-pip.py -Force; `
	Write-Host 'Verifying pip install ...'; `
	pip --version; `
	Write-Host 'Complete.'


# install MinGit
ENV GIT_VERSION 2.23.0

RUN $gitTag = ('v{0}.windows.1' -f $env:GIT_VERSION); `
    $gitUrl = ('https://github.com/git-for-windows/git/releases/download/{0}/MinGit-{1}-64-bit.zip' -f $gitTag, $env:GIT_VERSION); `
    $gitSHA356 = ('8f65208f92c0b4c3ae4c0cf02d4b5f6791d539cd1a07b2df62b7116467724735'); `
    Write-Host ('Downloading {0} ...' -f $gitUrl); `
	[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12; `
	Invoke-WebRequest -Uri $gitUrl -OutFile 'git.zip'; `
	Write-Host ('Verifying download ...'); `
	if ((Get-FileHash git.zip -Algorithm sha256).Hash -ne $gitSHA356) { `
		Write-Host 'FAILED!'; `
		exit 1; `
	}; `
	Write-Host 'Expanding ...'; `
	Expand-Archive -Path git.zip -DestinationPath C:\git\.; `
	Write-Host 'Updating PATH ...'; `
	$env:PATH = 'C:\git\cmd;C:\git\mingw64\bin;C:\git\usr\bin;' + $env:PATH; `
	[Environment]::SetEnvironmentVariable('PATH', $env:PATH, [EnvironmentVariableTarget]::Machine); `
	Write-Host 'Verifying install ...'; `
    Write-Host '  git version'; git version; `
	Write-Host 'Removing ...'; `
	Remove-Item git.zip -Force; `
	Write-Host 'Complete.';

RUN pip install -U pip setuptools wheel ;

####################################################################################################
#
# DAGSTER BUILDKITE INTEGRATION IMAGE
#
####################################################################################################

FROM dagster-base-image AS dagster-integration-image

ADD snapshot-reqs-${PYTHON_MAJOR_VERSION}.txt ./snapshot-reqs.txt
RUN pip install tox ; `
    pip install --trusted-host files.pythonhosted.org -r ./snapshot-reqs.txt; `
    Remove-Item ./snapshot-reqs.txt -Force;
