"use strict";
console.clear();

const { desk, qx, THREE, ACVD } = window;

const params = {
//    dir1 : "indiana/incisor",
//    dir2 : "DeepSDFModels/13",
    dir1 : "openData/Surfaces externes",
    dir2 : "DeepSDFModels/56",
    maxDistance : 0.5,
    direction : 0,
    ...window?.DeepSDF?.diffToolParams,
};

desk.URLParameters.parseParameters( params );
const viewer = new desk.THREE.Viewer();
if ( desk.auto ) viewer.fillScreen();
const viewer2 = new desk.THREE.Container();
viewer2.link( viewer );
viewer.getWindow().add( viewer2, { flex : 1 } );
const container = new qx.ui.container.Composite();
container.setLayout( new qx.ui.layout.VBox( 5 ) );
container.setWidth( 200 );
viewer.getWindow().addAt( container, 0 );
const dir1 = new desk.FileField( params.dir1 );
container.add( new qx.ui.basic.Label( "Database directory:") );
container.add( dir1 );
dir1.addListener( "changeValue", updateList );
const dir2 = new desk.FileField( params.dir2 );
container.add( new qx.ui.basic.Label( "Reconstructions directory:") );
container.add( dir2 );
dir2.addListener( "changeValue", updateList );
const list = new qx.ui.form.List();
container.add( new qx.ui.basic.Label( "Reconstructions:") );
container.add( list, { flex : 1  } );
const viewers = [ viewer, viewer2 ];
const colorBar = ACVD.getColorBar( params.maxDistance );
const downloadButton = new qx.ui.form.Button( "Downoad Mesh" );
downloadButton.addListener( "execute", () => {
    ACVD.downloadOBJ( reconstruction, list.getSelection()[ 0 ].getLabel() + ".obj" );
} );
viewer2.add( downloadButton, { bottom : 5, left : "30%" } );

const directionButton = new qx.ui.form.Button( "switch direction");
directionButton.addListener( "execute", () => {
    params.direction = 1- params.direction;
    updateList();
});
container.add( directionButton );

let meshes1, meshes2;

list.addListener("changeSelection", async function (e) {
    try{
        container.setEnabled( false );
        const selection = e.getData();
        viewer.removeAllMeshes();
        viewer2.removeAllMeshes();
    
        if ( selection[ 0 ] ) {

            const label = selection[ 0 ].getLabel();
            const meshes = [ meshes1[ label ], meshes2[ label ] ];
            const distance = await ACVD.getDistanceBetweenMeshes(
                meshes[ params.direction ], meshes[ 1 - params.direction ] );

            viewers[ 1 - params.direction ].addFileAsync( meshes[ 1 - params.direction ] );
            const promise = viewers[ params.direction ].addFileAsync( meshes[ 1-params.direction ] );
            original = await ACVD.loadMeshWithColors( distance, params.maxDistance, { label : "reconstruction" } );
            viewers[ params.direction ].addMesh( original );
            reconstruction = await promise;
            updateVisibilities();
            viewers[ params.direction ].add( colorBar, { bottom : 50, left : "10%", width : "80%" } );

        }
    } catch( e ) {
        console.warn( e );
        
    } finally {
        container.setEnabled( true );

    }
});

async function updateList() {

    list.removeAll();
    meshes1 = await getMeshes( dir1.getValue() );
    meshes2 = await getMeshes( dir2.getValue() );
    const meshArray = Object.keys( meshes1 );
    meshArray.sort();

    for ( let mesh of meshArray ) {

        if ( !meshes2[ mesh ] ) continue;
        const item = new qx.ui.form.ListItem( mesh );
        list.add(item);

    }

    list.setSelection( [ list.getChildren()[ 0 ] ] );

}

let original, reconstruction;
const switchView = new qx.ui.form.CheckBox( "switch" );
viewer.add( switchView, { left : 10, bottom : 5 } );
switchView.addListener( "changeValue", updateVisibilities );
const showBoth = new qx.ui.form.CheckBox( "show both" );
viewer.add( showBoth, { left : 10, bottom : 25 } );
showBoth.addListener( "changeValue", updateVisibilities );

function updateVisibilities() {

    if ( !reconstruction ) return;
    const meshes = switchView.getValue() ? [ reconstruction, original ] : [ original, reconstruction ];
    reconstruction.material.color.set( "yellow" );
    const [ m1, m2 ] = meshes;
    m1.material.opacity = 1;
    m1.material.transparent = false;
    m1.visible = true;
    m1.renderOrder = 1;
    m2.material.opacity = 0.2;
    m2.material.transparent = true;
    m2.visible = showBoth.getValue();
    m2.renderOrder = 2;
    viewer.render();

}

updateList().catch( console.warn );

async function getMeshes( dir ) {

    const files = {};
    await desk.FileSystem.traverseAsync( dir, file => {

        for ( let extension of [ ".stl", ".ply" ] )
            if ( file.toLowerCase().endsWith( extension ) ) {
                const name = file.split( "/" ).pop()
                    .split( "." )[ 0 ]
                    .split( " " ).join( "_" );
                files[ name ] = file;
            }

    } );

    return files;

}
