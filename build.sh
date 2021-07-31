ROOT=$(PWD)
mkdir output -p

cd pd/pd-server
go build -o $ROOT/output/pd.exe
echo "build pd success"

cd $ROOT
cd gateway/Gateway

echo $(PWD)

dotnet publish -c Release -r win-x64 -p:PublishSingleFile=true --self-contained
cd bin/Release/net5.0/win-x64/publish/
ls -al
tar -cjf gateway.tar.bz2 Gateway.* *.dll *.config *.json
mv gateway.tar.bz2 $ROOT/output/

echo "build gateway success"


cd $ROOT
cp -r koala output
cd output/koala
find . -iname "__pycache__" | xargs rm -rf

cd $ROOT/output
tar -cjf koala.tar.bz2 koala
rm koala -rf

echo "build koala success"

sleep 5